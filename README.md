# EvalForge

A small framework for defining, running, and scoring agentic tasks — to measure
agent reliability over time.

You describe a task (input + what tools/output you expect), point an agent
adapter at it, and EvalForge runs the agent, scores the run on several axes, and
persists the results to JSONL + SQLite so you can track trends across runs.

## Install

Uses [uv](https://docs.astral.sh/uv/). A venv is assumed to exist.

```
uv pip install -e ".[dev]"
```

Sanity check:

```
uv run python -c "import evalforge; print(evalforge.__version__)"   # -> 0.1.0
```

## Quickstart

Run the bundled example task against the reference `EchoAgent`, then view trends.
Run from the repo root (so `adapters.*` resolves).

```
uv run pytest
uv run evalforge run --tasks tasks/ --agent adapters.example_echo:EchoAgent
uv run evalforge report
```

`run` prints one scored summary line per task and writes:

- `results/<agent>_<task>.jsonl` — one JSON object per run (append-only).
- `results/results.db` — SQLite `runs` table, one row per run.

`report` aggregates per task across all stored runs (run count, average
completion, average latency). Run `run` again, then `report`, to see the
averages move.

### CLI reference

```
evalforge run      --tasks PATH --agent module:ClassName [--out DIR]
evalforge report   [--task ID] [--agent NAME] [--out DIR]
evalforge generate (--category KEY | --all) [--count N] [--dry-run] [--out DIR]
```

- `--tasks` — a single `*.yaml` task file, a directory of them (searched
  **recursively**), or the literal `all` (= everything under `tasks/`).
- `--agent` — adapter spec `"module.path:ClassName"`, e.g.
  `adapters.example_echo:EchoAgent`.
- `--out` — results directory (default `results`).

## Scorers

Each run is scored by the registry in
[src/evalforge/scoring/registry.py](src/evalforge/scoring/registry.py):

| Scorer          | Meaning                                                     |
|-----------------|-------------------------------------------------------------|
| `completion`    | 1.0 if output non-empty and contains expected strings       |
| `tool_accuracy` | fraction of expected tool calls matched                     |
| `latency`       | wall-clock run latency in ms (raw)                          |
| `token_cost`    | estimated USD cost from token usage (raw)                   |
| `judge`         | LLM-as-judge (local Ollama) graded 0..1 against a rubric    |
| `hallucination` | fraction of asserted claims grounded in actual tool results |

`judge` calls a local [Ollama](https://ollama.com) model — set by
`EVALFORGE_JUDGE_MODEL` (default `llama3.2`). Ollama must be running for a
non-zero `judge` score; if it is down or the model is missing, the run still
completes and `judge` scores `0.0` with the error in its details.

## Writing an adapter

An adapter is any object with a `name` attribute and a
`run(self, task_input: str) -> AgentRun` method. Return the agent's output, the
tool calls it made, and token usage. See
[adapters/example_echo.py](adapters/example_echo.py) for the reference:

```python
from evalforge.agent import AgentRun, ToolCall, TokenUsage


class MyAgent:
    name = "MyAgent"

    def run(self, task_input: str) -> AgentRun:
        # ... call your real agent here ...
        return AgentRun(
            output="the agent's answer",
            tool_calls=[ToolCall("web_search", {"query": task_input})],
            token_usage=TokenUsage(input_tokens=10, output_tokens=20),
        )
```

Point the CLI at it with `--agent your_module:MyAgent` (run from the directory
where `your_module` is importable).

## Defining a task

A task is a YAML file. See [tasks/example_task.yaml](tasks/example_task.yaml):

```yaml
id: echo_web_search
description: Echo agent should restate the input and call web_search once.
input: search for echo chambers
expected_tools:
  - name: web_search
    args:
      query: "*"        # "*" = any value, key must be present
expected_output:
  contains:
    - echo
metadata:
  tags: [smoke, example]
```

## Generating adversarial tasks

`evalforge generate` uses a local [Ollama](https://ollama.com) model to write
hard, edge-case tasks, validates them, maps them to the real task schema, and
saves them to `tasks/generated/`. Five categories, each stressing a different
agent failure mode:

| Category            | What it stresses                                            |
|---------------------|-------------------------------------------------------------|
| `ambiguous`         | unclear goal, multiple valid interpretations                |
| `conflicting_tools` | two tools return contradictory information                  |
| `missing_context`   | references info the agent can't access                      |
| `overloaded`        | too many sub-goals packed into one instruction              |
| `adversarial_input` | subtle prompt injection embedded in the `input` string      |

```
ollama pull llama3.2
uv run evalforge generate --category ambiguous --count 3 --dry-run
uv run evalforge generate --all --count 2
uv run evalforge run --tasks all --agent adapters.example_echo:EchoAgent
```

- `--category KEY` / `--all` — one category (choices above) or all five
  (mutually exclusive, one required).
- `--count N` — tasks to request per category (default 5). Weak local models may
  return fewer; malformed tasks are dropped by the validator.
- `--dry-run` — print the mapped YAML, write nothing.
- `--out DIR` — output directory (default `tasks/generated`).

Generation calls Ollama, set by `EVALFORGE_GEN_MODEL` (default `llama3.2`);
**Ollama must be running** for live generation. If it is down or returns
unparseable output, `generate` retries once then reports `0 saved` — it never
crashes. Generated files use the real schema (`id`/`input`/`expected_output`/
`metadata`, with `failure_indicators` under `metadata`), so they load and run
exactly like hand-written tasks.

## Prompt Versioning

EvalForge includes **PromptVault** — a built-in version-control system for
prompts. Track every change, compare versions side-by-side, run A/B tests, and
roll back to any previous version — all from the CLI.

### Quick example

```bash
# 1. Start tracking a prompt file
evalforge prompt init prompts/example_system.txt

# 2. Edit the file, then commit the change
evalforge prompt commit example_system prompts/example_system.txt -m "add citation rule"

# 3. Run your eval suite tagged to the active prompt version
evalforge run --tasks tasks/ --agent adapters.example_echo:EchoAgent --prompt example_system

# 4. View version history
evalforge prompt log example_system

# 5. Roll back to an earlier version
evalforge prompt rollback example_system <hash>
```

### A/B testing

Compare two prompt versions head-to-head across your full task suite:

```bash
evalforge ab --agent adapters.example_echo:EchoAgent \
             --prompt-a example_system \
             --prompt-b example_system_v2 \
             --tasks tasks/
```

This runs every task twice (once per prompt), persists all results, and prints a
per-task comparison table showing the delta for each metric.

### `prompt` subcommand reference

| Subcommand               | Description                                     |
|---------------------------|-------------------------------------------------|
| `prompt init <file>`      | Start tracking a prompt file                    |
| `prompt commit <name> <file> -m MSG` | Snapshot current file as a new version |
| `prompt log <name>`       | Show version history for a prompt               |
| `prompt show <hash>`      | Print the content of a specific version         |
| `prompt diff <hash1> <hash2>` | Unified diff between two versions           |
| `prompt rollback <name> <hash>` | Set active version (and rewrite file)      |
| `prompt list`             | List all tracked prompts                        |
| `prompt active <name>`    | Print the active version hash                   |
| `prompt set-active <name> <hash>` | Manually set the active version          |

### Backward compatibility

The `--prompt` flag on `evalforge run` is **optional**. If omitted,
`prompt_version` stays empty and behaviour is identical to before PromptVault
was added — no existing workflows break.

## Project layout

```
src/evalforge/         core: task, agent contract, runner, store, report, cli
src/evalforge/scoring/ scorers + registry
src/evalforge/prompts/ prompt versioning (store, vault, diff, a/b testing)
generator/             adversarial task generator (categories, validator, Ollama seam)
adapters/              agent adapters (example_echo)
tasks/                 task definitions (tasks/generated/ = machine-generated)
prompts/               example prompt files
tests/                 pytest suite
```
