from pathlib import Path

from generator.categories import Category



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
    
    # generate --category ambiguous --count 2 --dry-run with _chat monkeypatched → exits clean, writes nothing; --category and --all together → argparse error.
    
def test_cli_generate(monkeypatch):
    import json

    from evalforge.cli import cmd_generate

    class Args:
        category = "ambiguous"
        count = 2
        model = "gpt-4"

    def mock_chat(model, messages, **kwargs):
        assert model == "gpt-4"
        return json.dumps([
            {
                "id": f"task-{i}",
                "input": f"input {i}",
                "description": f"description {i}",
                "expected_tools": [],
                "expected_output": {},
                "metadata": {},
            }
            for i in range(Args.count)
        ])

    import generator.generator
    monkeypatch.setattr(generator.generator, "_chat", mock_chat)
    cmd_generate(Args())
    
    
    
    
    
    
    
    
    
    


