# EvalForge v2 — Implementation Guide

Two new scorers, append-only. No refactor of v1. You write the bodies.
Tooling: **uv** (venv already created). `ollama` dep already added to
[pyproject.toml](pyproject.toml).

Legend: 📄 file to create · ✍️ what to write · 🧪 test · ▶️ run

v2 = `JudgeScorer` (LLM-as-judge on local **Ollama**) + `HallucinationScorer`
(deterministic, no LLM). Both just append to
[registry.py](src/evalforge/scoring/registry.py) — runner, store, report, CLI unchanged.

---

## Why nothing else changes (read first)

Facts from the v1 code that shape these scorers:

- `scores`/`details` persist as **JSON-text columns** in SQLite
  ([store.py](src/evalforge/store.py) `SCHEMA`). New scorer keys land there
  automatically — **no DB migration**.
- The runner names each score by its **registry dict key**, not the scorer's `.name`
  ([runner.py:36-39](src/evalforge/runner.py#L36)). So you wire scorers in by key.
- Scorers run **outside** the runner's `try/except`
  ([runner.py:35](src/evalforge/runner.py#L35)). A scorer that raises crashes the whole
  run → **`JudgeScorer` must catch its own errors and never re-raise**.
- [registry.py](src/evalforge/scoring/registry.py) imports every scorer at module load.
  So **lazy-import `ollama` inside the call**, not at module top — a dead daemon or
  missing model must degrade gracefully, not break the framework on import.
- Real field names: `ToolCall.results` (plural,
  [agent.py:8](src/evalforge/agent.py#L8)), `AgentRun.token_usage`,
  `Score(name, value, details)` — `details` has **no default**, always pass it.
- No-input convention: when a scorer has nothing to score, return `value=1.0` with a
  `note` in details (see `ToolAccuracyScorer`'s empty-`expected` path,
  [tool_accuracy.py:22](src/evalforge/scoring/tool_accuracy.py#L22)).

---

## Step 16 — Judge scorer (LLM-as-judge via Ollama)

📄 [src/evalforge/scoring/judge.py](src/evalforge/scoring/judge.py)

✍️ A testable Ollama seam + the scorer:

- Module-level `_chat(model, messages) -> str` — the **only** thing that touches Ollama,
  so tests can monkeypatch it. Body: `import ollama` (lazy, inside the function),
  `resp = ollama.chat(model=model, messages=messages, format="json",
  options={"temperature": 0})`, return the message content string
  (`resp["message"]["content"]`).
- `JudgeScorer`, `name = "JudgeScorer"`. `score(self, task, agent_run) -> Score`:
  1. `rubric = task.expected_output.get("rubric")`. Falsy → `Score(self.name, 1.0,
     {"note": "no rubric"})`.
  2. `model = os.environ.get("EVALFORGE_JUDGE_MODEL", "llama3.1")`. (Host/port come from
     the `ollama` package's own `OLLAMA_HOST` env — don't reinvent.)
  3. Build `messages`: a **system** turn ("You are a strict grader. Given a rubric and an
     agent's answer, return JSON `{\"score\": <float 0..1>, \"reason\": <str>}` and
     nothing else.") and a **user** turn carrying `task.input`, the `rubric`, and
     `agent_run.output`.
  4. `raw = _chat(model, messages)`; `data = json.loads(raw)`; pull `score`, clamp to
     `[0,1]` (`max(0.0, min(1.0, float(...)))`); keep `reason`.
  5. Return `Score(self.name, score, {"reason": ..., "model": model})`.
  - **Wrap steps 2–5 in `try/except Exception as e`** → on any failure (package missing,
    connection refused, bad JSON) return `Score(self.name, 0.0, {"error": str(e),
    "model": model})`. Never let it propagate.

Imports: `json`, `os`, `Score`/`Scorer` from
[base.py](src/evalforge/scoring/base.py). (`import ollama` stays inside `_chat`.)

Decision baked in: judge failure scores `0.0` (numeric, averages conservatively) with the
reason visible in `details["error"]`.

🧪 [tests/test_judge.py](tests/test_judge.py) — monkeypatch
`evalforge.scoring.judge._chat`, never hit a live Ollama:
- no `rubric` in task → `value == 1.0`.
- `_chat` returns `'{"score": 0.8, "reason": "ok"}'` → `value == 0.8`, reason in details.
- `_chat` raises → `value == 0.0`, `"error"` in details, **no exception escapes**.
- `_chat` returns `'{"score": 1.5, ...}'` → clamped to `1.0`.

---

## Step 17 — Hallucination scorer (deterministic)

📄 [src/evalforge/scoring/hallucination.py](src/evalforge/scoring/hallucination.py)

✍️ `HallucinationScorer`, `name = "HallucinationScorer"`. Pure string matching, same idiom
as `expected_output.contains`. `score(self, task, agent_run) -> Score`:

- `claims = task.expected_output.get("grounded_claims", [])` — author-listed facts the
  answer may assert that must be backed by tool output. Empty → `Score(self.name, 1.0,
  {"note": "no claims"})`.
- `evidence = "\n".join(str(tc.results) for tc in agent_run.tool_calls)` — note
  `.results` (plural).
- `asserted = [c for c in claims if c in agent_run.output]` — claims the agent made.
- `hallucinated = [c for c in asserted if c not in evidence]` — asserted but unsupported.
- `value = 1.0` if `asserted` is empty, else `1.0 - len(hallucinated) / len(asserted)`.
- Return `Score(self.name, value, {"asserted": asserted, "hallucinated": hallucinated})`.

A claim counts against the agent only if it **made** the claim **and** no tool result
supports it — that's the hallucination signal.

🧪 [tests/test_hallucination.py](tests/test_hallucination.py):
- no `grounded_claims` → `1.0`.
- asserted claim present in evidence → `1.0`.
- asserted claim absent from evidence → `< 1.0`, listed in `details["hallucinated"]`.
- claim not present in output → ignored (still `1.0`).

Build `AgentRun`/`ToolCall` fixtures inline (set `results=` on a `ToolCall` to seed
evidence).

---

## Step 18 — Wire into the registry

📄 [src/evalforge/scoring/registry.py](src/evalforge/scoring/registry.py)

✍️ Import the two classes; add to `DEFAULT_SCORERS`:
```python
"judge": JudgeScorer(),
"hallucination": HallucinationScorer(),
```
Nothing else. Runner picks them up by key; store/report serialize the values as JSON.

🧪 Assert (in any registry test or a new one) that `"judge"` and `"hallucination"` are
keys in `DEFAULT_SCORERS`.

---

## Step 19 — Fixture task

📄 [tasks/judged_task.yaml](tasks/judged_task.yaml)

✍️ Same keys as [example_task.yaml](tasks/example_task.yaml), plus an `expected_output`
that exercises both scorers:
- `rubric:` a one-line grading instruction (e.g. "The answer restates the user's query").
- `grounded_claims:` a list of short strings that should appear in tool results if the
  agent cites them.

Pick `input`/`expected_tools` so `EchoAgent` ([adapters/example_echo.py](adapters/example_echo.py))
produces gradeable output.

---

## Step 20 — Verify end-to-end

▶️ Offline first (tests mock the `_chat` seam — no Ollama needed):
```
uv run pytest
```
▶️ Live judge path (one-time model pull, then run):
```
ollama pull llama3.1
uv run evalforge run --tasks tasks/judged_task.yaml --agent adapters.example_echo:EchoAgent
uv run evalforge report
```
✅ Expect: pytest green; `results/EchoAgent_judged_task.jsonl` carries `judge` +
`hallucination` inside the `scores`/`details` objects; the SQLite `scores` JSON column
includes both keys (no schema change). With Ollama **down**, the run still completes and
`judge` shows `0.0` + an `error` detail instead of crashing.

🧪 Spot-check: kill the Ollama daemon, re-run `run` → no traceback, `judge=0.00` in the
summary line, run still persisted.

---

## Step 21 — Docs (optional now)

📄 [README.md](README.md) — add two rows to the scorer table:

| Scorer          | Meaning                                                        |
|-----------------|----------------------------------------------------------------|
| `judge`         | LLM-as-judge (local Ollama) graded 0..1 against a rubric       |
| `hallucination` | fraction of asserted claims grounded in actual tool results    |

Note the `EVALFORGE_JUDGE_MODEL` env var (default `llama3.1`) and that Ollama must be
running for a non-zero `judge` score.
