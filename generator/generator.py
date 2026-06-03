import json
import logging
import os
from dataclasses import dataclass, field

from generator.categories import Category
from generator.validator import save_yaml, to_evalforge_yaml, validate

log = logging.getLogger(__name__)

MODEL = os.environ.get("EVALFORGE_GEN_MODEL", "llama3.2")


def _chat(model: str, messages: list[dict]) -> str:
    """Only thing touching Ollama. Lazy import so a dead daemon degrades, not crashes."""
    import ollama

    resp = ollama.chat(
        model=model,
        messages=messages,
        format="json",
        options={"temperature": 0},
    )
    return resp["message"]["content"]


def build_prompt(category: Category, count: int) -> list[dict]:
    system = (
        "You generate hard, adversarial agent-evaluation tasks. "
        "Return ONLY a JSON array, no preamble, no markdown fence."
    )
    user = (
        f"Generate {count} genuinely hard tasks for the category "
        f"'{category.name}': {category.description}\n"
        f"What makes this category hard: {category.guidance}\n\n"
        "Each task is a JSON object with these fields:\n"
        "  task_id (unique string),\n"
        "  description (why this task is hard),\n"
        "  input (the instruction given to the agent),\n"
        "  expected_tools (list of {name, args}),\n"
        "  expected_output_contains (non-empty list of strings),\n"
        "  rubric (short grading guidance),\n"
        "  failure_indicators (non-empty list of strings — signs the agent failed),\n"
        "  timeout_seconds (int).\n\n"
        "Rules: every task MUST include failure_indicators. expected_tools must be "
        "a list of OBJECTS, each {\"name\": \"<tool>\", \"args\": {...}} — never a list "
        "of strings. Tasks must be genuinely hard, not trivial edge cases.\n\n"
        "Example of ONE well-formed task:\n"
        "{\n"
        '  "task_id": "ambiguous-1",\n'
        '  "description": "why this is hard",\n'
        '  "input": "the instruction",\n'
        '  "expected_tools": [{"name": "search", "args": {"query": "x"}}],\n'
        '  "expected_output_contains": ["term a", "term b"],\n'
        '  "rubric": "how to grade",\n'
        '  "failure_indicators": ["sign of failure"],\n'
        '  "timeout_seconds": 60\n'
        "}\n\n"
        "Return a JSON array of such objects only."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_tasks(raw: str) -> list[dict]:
    """Accept a top-level list, {"tasks": [...]}, or a single task object.

    Local models under format="json" often emit one bare task object instead of
    an array, so a lone task dict is wrapped into a one-element list.
    """
    data = json.loads(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("tasks"), list):
            return data["tasks"]
        if "task_id" in data:
            return [data]
    raise ValueError("expected a JSON array, {'tasks': [...]}, or a task object")


def generate(category: Category, count: int, model: str = MODEL) -> list[dict]:
    """build_prompt -> _chat -> parse_tasks. Retry once, then return [] (no raise)."""
    messages = build_prompt(category, count)
    for attempt in (1, 2):
        try:
            return parse_tasks(_chat(model, messages))
        except (json.JSONDecodeError, ValueError) as e:
            log.warning("generate %s attempt %d failed: %s", category.key, attempt, e)
    log.error("generate %s gave up after 2 attempts", category.key)
    return []


@dataclass
class Report:
    saved: int = 0
    skipped: int = 0
    per_category: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)


def run_generation(
    categories: list[Category],
    count: int,
    dry_run: bool,
    out_dir: str,
    model: str = MODEL,
) -> Report:
    report = Report()
    for cat in categories:
        saved = skipped = 0
        for task in generate(cat, count, model):
            problems = validate(task)
            if problems:
                skipped += 1
                log.warning("skipping task in %s: %s", cat.key, problems)
                continue
            mapped = to_evalforge_yaml(task, cat.key)
            if dry_run:
                import yaml

                print(yaml.safe_dump(mapped, sort_keys=False))
            else:
                save_yaml(mapped, out_dir)
            saved += 1
        report.saved += saved
        report.skipped += skipped
        report.per_category[cat.key] = {"saved": saved, "skipped": skipped}
    return report
