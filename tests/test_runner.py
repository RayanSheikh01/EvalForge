import pytest

from evalforge.agent import AgentRun, ToolCall, TokenUsage
from evalforge.runner import RunRecord, run_task, run_suite
from evalforge.task import Task


class FakeAgent:
    name = "fake"

    def run(self, input: str) -> AgentRun:
        return AgentRun(
            output=f"echo {input}",
            tool_calls=[ToolCall("web_search", {"query": input})],
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
        )


class BoomAgent:
    name = "boom"

    def run(self, input: str) -> AgentRun:
        raise RuntimeError("kaboom")


def _task():
    return Task(id="t1", input="hello", expected_output={"contains": ["echo"]})


def test_run_task_success():
    rec = run_task(FakeAgent(), _task())
    assert isinstance(rec, RunRecord)
    assert rec.task_id == "t1"
    assert rec.agent_name == "fake"
    assert rec.error == ""
    assert rec.latency_ms >= 0
    # all default scorers ran
    for key in ("completion", "tool_accuracy", "latency", "token_cost"):
        assert key in rec.scores
    assert rec.scores["completion"] == 1.0


def test_run_task_agent_raises():
    rec = run_task(BoomAgent(), _task())
    assert rec.error                      # traceback captured
    assert rec.scores["completion"] == 0.0
    assert rec.run.output == ""           # no crash, empty fallback run


def test_run_suite():
    recs = run_suite(FakeAgent(), [_task(), _task()])
    assert len(recs) == 2
    assert all(isinstance(r, RunRecord) for r in recs)
