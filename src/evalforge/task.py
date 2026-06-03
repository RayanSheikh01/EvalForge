from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ExpectedTool:
    name: str
    args: dict = field(default_factory=dict)


@dataclass
class Task:
    id: str
    input: str
    description: str = ""
    expected_tools: list[ExpectedTool] = field(default_factory=list)
    expected_output: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    @staticmethod
    def load_tasks(path: str) -> list["Task"]:
        return load_tasks(path)


def load_tasks(path: str) -> list[Task]:
    p = Path(path)
    files = sorted(p.glob("**/*.yaml")) if p.is_dir() else [p]
    tasks = []
    for f in files:
        d = yaml.safe_load(f.read_text())
        d["expected_tools"] = [
            ExpectedTool(**t) for t in d.get("expected_tools", [])
        ]
        tasks.append(Task(**d))
    return tasks




