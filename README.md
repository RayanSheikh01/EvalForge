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
evalforge run    --tasks PATH --agent module:ClassName [--out DIR]
evalforge report [--task ID] [--agent NAME] [--out DIR]
```

- `--tasks` — a single `*.yaml` task file or a directory of them.
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

## Project layout

```
src/evalforge/        core: task, agent contract, runner, store, report, cli
src/evalforge/scoring/ scorers + registry
adapters/             agent adapters (example_echo)
tasks/                task definitions
tests/                pytest suite
```
