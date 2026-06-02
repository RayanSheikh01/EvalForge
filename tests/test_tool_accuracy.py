import pytest

from evalforge.agent import AgentRun, ToolCall
from evalforge.scoring.tool_accuracy import ToolAccuracyScorer
from evalforge.task import ExpectedTool, Task


@pytest.mark.parametrize(
    "tool_name, expected_accuracy",
    [
        ("tool1", 1.0),
        ("tool2", 0.0),
    ],
)
def test_tool_accuracy(tool_name, expected_accuracy):
    scorer = ToolAccuracyScorer()

    expected_args = {"arg1": "value1", "arg2": "value2"}
    actual_args = (
        {"arg1": "value1", "arg2": "value2"}
        if tool_name == "tool1"
        else {"arg1": "wrong_value", "arg2": "value2"}
    )

    task = Task(
        id="t",
        input="",
        expected_tools=[ExpectedTool(name="search", args=expected_args)],
    )
    agent_run = AgentRun(
        output="",
        tool_calls=[ToolCall(name="search", args=actual_args)],
        token_usage=None,
    )

    score = scorer.score(task, agent_run)

    assert score.value == expected_accuracy, (
        f"Expected accuracy {expected_accuracy} but got {score.value} for {tool_name}"
    )
