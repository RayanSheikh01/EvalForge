import pytest

# invoke cmd_run against example task + EchoAgent in tmp_path, assert files written.

def test_cli_run(tmp_path):
    from src.evalforge.cli import cmd_run

    class Args:
        agent = "echo"
        input = "Hello, EvalForge!"
        output = str(tmp_path / "run_record.json")

    cmd_run(Args())

    assert (tmp_path / "run_record.json").exists(), "Run record file not found"
    
    
    
    
    