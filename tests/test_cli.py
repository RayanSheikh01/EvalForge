from pathlib import Path


# invoke cmd_run against example task + EchoAgent, assert files written to out dir.

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
