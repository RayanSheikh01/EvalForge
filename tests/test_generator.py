import json

from generator import generator
from generator.categories import CATEGORIES


def _valid_task(i: int = 1) -> dict:
    return {
        "task_id": f"task-{i}",
        "description": "hard task",
        "input": "do the thing",
        "expected_tools": [{"name": "tool1", "args": {}}],
        "expected_output_contains": ["answer"],
        "failure_indicators": ["wrong answer"],
        "timeout_seconds": 60,
    }


def test_generate_parses_json_array(monkeypatch):
    monkeypatch.setattr(generator, "_chat", lambda m, msgs: json.dumps([_valid_task()]))
    tasks = generator.generate(CATEGORIES["ambiguous"], 1)
    assert isinstance(tasks, list)
    assert tasks[0]["task_id"] == "task-1"


def test_generate_parses_tasks_object(monkeypatch):
    monkeypatch.setattr(
        generator, "_chat", lambda m, msgs: json.dumps({"tasks": [_valid_task()]})
    )
    tasks = generator.generate(CATEGORIES["ambiguous"], 1)
    assert tasks[0]["task_id"] == "task-1"


def test_generate_garbage_twice_returns_empty(monkeypatch):
    monkeypatch.setattr(generator, "_chat", lambda m, msgs: "not json at all")
    assert generator.generate(CATEGORIES["ambiguous"], 1) == []


def test_run_generation_counts_and_dry_run_writes_nothing(monkeypatch, tmp_path):
    invalid = _valid_task(2)
    del invalid["failure_indicators"]
    monkeypatch.setattr(
        generator, "_chat", lambda m, msgs: json.dumps([_valid_task(1), invalid])
    )
    report = generator.run_generation(
        [CATEGORIES["ambiguous"]], count=2, dry_run=True, out_dir=str(tmp_path)
    )
    assert report.saved == 1
    assert report.skipped == 1
    assert not list(tmp_path.iterdir())  # dry-run writes nothing
