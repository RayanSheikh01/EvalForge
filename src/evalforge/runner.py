import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone

from evalforge.agent import AgentRun, TokenUsage
from evalforge.scoring.registry import DEFAULT_SCORERS


@dataclass
class RunRecord:
    run_id: str
    task_id: str
    agent_name: str
    ts: str
    latency_ms: float
    run: AgentRun
    scores: dict = field(default_factory=dict)
    details: dict = field(default_factory=dict)
    error: str = ""


def run_task(agent, task, scorers=DEFAULT_SCORERS) -> RunRecord:
    t0 = time.perf_counter()
    error = ""
    try:
        run = agent.run(task.input)
    except Exception:
        error = traceback.format_exc()
        run = AgentRun(output="", tool_calls=[], token_usage=TokenUsage())
    latency_ms = (time.perf_counter() - t0) * 1000
    run.latency_ms = latency_ms
    run.error = error

    scores, details = {}, {}
    for key, scorer in scorers.items():
        sc = scorer.score(task, run)
        scores[key] = sc.value
        details[key] = sc.details

    return RunRecord(
        run_id=f"{task.id}-{int(time.time() * 1000)}",
        task_id=task.id,
        agent_name=agent.name,
        ts=datetime.now(timezone.utc).isoformat(),
        latency_ms=latency_ms,
        run=run,
        scores=scores,
        details=details,
        error=error,
    )


def run_suite(agent, tasks, scorers=DEFAULT_SCORERS) -> list[RunRecord]:
    return [run_task(agent, t, scorers) for t in tasks]
