from evalforge.task import load_tasks
from generator.validator import save_yaml, to_evalforge_yaml, validate


def _complete_task() -> dict:
    return {
        "task_id": "test_task",
        "description": "A test task",
        "input": "Test input",
        "expected_tools": [{"name": "tool1", "args": {"arg1": "value1"}}],
        "expected_output_contains": ["expected output"],
        "failure_indicators": ["indicator1"],
        "timeout_seconds": 30,
    }


def test_validate_complete_task():
    assert validate(_complete_task()) == []


def test_validate_missing_failure_indicators():
    task = _complete_task()
    del task["failure_indicators"]
    problems = validate(task)
    assert problems
    assert any("failure_indicators" in p for p in problems)


def test_to_evalforge_yaml_shape():
    mapped = to_evalforge_yaml(_complete_task(), "ambiguous")
    assert mapped["id"] == "test_task"
    assert "task_id" not in mapped
    assert mapped["expected_output"]["contains"] == ["expected output"]
    assert mapped["metadata"]["failure_indicators"] == ["indicator1"]
    assert "scoring" not in mapped
    assert "timeout_seconds" not in mapped
    assert mapped["metadata"]["timeout_seconds"] == 30


def test_save_yaml_round_trips_through_load_tasks(tmp_path):
    mapped = to_evalforge_yaml(_complete_task(), "ambiguous")
    path = save_yaml(mapped, str(tmp_path))
    tasks = load_tasks(path)  # must not raise TypeError
    assert tasks[0].id == "test_task"
