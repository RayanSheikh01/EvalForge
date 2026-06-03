import pytest
from src.evalforge.task import Task, ExpectedTool
from generator.validator import validate


def test_validator():
    from generator.validator import validate
    from src.evalforge.task import Task
    expected_tools = [ExpectedTool(name="tool1", args={"arg1": "value1"})]
    task = Task(
        id="test_task",
        description="A test task",
        input="Test input",
        expected_tools=expected_tools,
        expected_output={"contains": ["expected output"]},
        metadata={"failure_indicators": ["indicator1"]}
    )
    errors = validate(task)
    assert errors == []