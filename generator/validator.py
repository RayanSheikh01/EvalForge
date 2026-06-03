import re
from pathlib import Path

import yaml

REQUIRED = (
    "task_id",
    "description",
    "input",
    "expected_tools",
    "expected_output_contains",
    "failure_indicators",
)


def validate(task: dict) -> list[str]:
    """Return a list of problem strings (empty = valid). Never raises."""
    problems: list[str] = []

    for key in REQUIRED:
        if key not in task or not task[key]:
            problems.append(f"missing or empty required field: {key}")

    tools = task.get("expected_tools")
    if isinstance(tools, list):
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict) or "name" not in tool:
                problems.append(f"expected_tools[{i}] must be a dict with a 'name'")
    elif tools is not None:
        problems.append("expected_tools must be a list")

    for key in ("expected_output_contains", "failure_indicators"):
        val = task.get(key)
        if val is not None and (not isinstance(val, list) or not val):
            problems.append(f"{key} must be a non-empty list")

    return problems


def to_evalforge_yaml(task: dict, category_key: str) -> dict:
    """Map rich generated JSON -> the real EvalForge Task schema."""
    expected_output: dict = {"contains": task["expected_output_contains"]}
    if "rubric" in task:
        expected_output["rubric"] = task["rubric"]

    return {
        "id": task["task_id"],
        "description": task["description"],
        "input": task["input"],
        "expected_tools": [
            {"name": t["name"], "args": t.get("args", {})}
            for t in task["expected_tools"]
        ],
        "expected_output": expected_output,
        "metadata": {
            "tags": ["generated", category_key],
            "category": category_key,
            "failure_indicators": task["failure_indicators"],
            "timeout_seconds": task.get("timeout_seconds", 60),
            "generated": True,
        },
    }


def save_yaml(mapped: dict, out_dir: str) -> str:
    """Write mapped task to <out_dir>/<slug>.yaml, dedupe collisions, return path."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^a-z0-9_-]", "-", str(mapped["id"]).lower()).strip("-") or "task"

    path = out / f"{slug}.yaml"
    n = 2
    while path.exists():
        path = out / f"{slug}-{n}.yaml"
        n += 1

    path.write_text(yaml.safe_dump(mapped, sort_keys=False))
    return str(path)
