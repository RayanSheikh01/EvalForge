
from evalforge.task import Task


REQUIRED = ("id", "description", "input", "expected_tools", "expected_output", "metadata")

def validate(task: Task) -> list[str]:
    errors = []
    for key in REQUIRED:
        if not hasattr(task, key):
            errors.append(f"Missing required field: {key}")
        
    return errors

def to_evalforge_yaml(task: Task, category_key: str) -> dict:
    return {
        "id": [task.id],
        "description": task.description,
        "input": task.input,
        "expected_tools": [
            {"name": tool.name, "args": tool.args}
            for tool in task.expected_tools
        ],
        "expected_output": {
            "contains": task.expected_output.get("contains", [])
        },
        "metadata": {
            "failure_indicators": task.expected_output.get("failure_indicators", []),
            "category": category_key
        }
    }


def save_yaml(task: dict, path: str):
    import yaml
    from pathlib import Path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        yaml.dump(task, f, sort_keys=False)

