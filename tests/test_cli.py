import json
import sys
from pathlib import Path

import pytest


def test_cli_run(tmp_path):
    from evalforge.cli import cmd_run

    repo_root = Path(__file__).resolve().parent.parent

    class Args:
        agent = "adapters.example_echo:EchoAgent"
        tasks = str(repo_root / "tasks" / "example_task.yaml")
        out = str(tmp_path)

    cmd_run(Args())

    jsonl_files = list(tmp_path.glob("*.jsonl"))
    assert jsonl_files, "No JSONL run record written"
    assert (tmp_path / "results.db").exists(), "SQLite results.db not found"


def test_cli_generate_dry_run_writes_nothing(monkeypatch, tmp_path):
    from evalforge.cli import cmd_generate

    class Args:
        category = "ambiguous"
        all = False
        count = 2
        dry_run = True
        out = str(tmp_path)

    def mock_chat(model, messages):
        return json.dumps(
            [
                {
                    "task_id": f"task-{i}",
                    "description": f"description {i}",
                    "input": f"input {i}",
                    "expected_tools": [{"name": "tool1", "args": {}}],
                    "expected_output_contains": ["answer"],
                    "failure_indicators": ["wrong"],
                    "timeout_seconds": 60,
                }
                for i in range(Args.count)
            ]
        )

    import generator.generator

    monkeypatch.setattr(generator.generator, "_chat", mock_chat)
    cmd_generate(Args())
    assert not list(tmp_path.iterdir())  # dry-run writes nothing


def test_cli_generate_category_and_all_is_argparse_error(monkeypatch):
    from evalforge.cli import main

    monkeypatch.setattr(
        sys, "argv", ["evalforge", "generate", "--category", "ambiguous", "--all"]
    )
    with pytest.raises(SystemExit):
        main()
