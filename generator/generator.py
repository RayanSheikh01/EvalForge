import ollama   

from generator.categories import Category
from dataclasses import dataclass, field
from evalforge.task import Task, ExpectedTool
from generator.validator import to_evalforge_yaml, validate

def _chat(model: str, messages: list[dict[str, str]], **kwargs) -> str:
    resp = ollama.chat(model=model, messages=messages, format="json", options={"temperature": 0}, **kwargs)
    return resp["message"]["content"]
    
def build_prompt(category: Category, count: int) -> list[dict[str, str]]:
    system_prompt = "You generate hard, adversarial agent-evaluation tasks. Return ONLY a JSON array, no preamble, no markdown fence."
    user_prompt = f"""Generate {count} tasks in the category '{category.name}'. Each task should be a JSON object with fields: 'id' (a unique string), 'input' (the question or problem statement), 'description' (a detailed explanation of the task, optional), 'expected_tools' (a list of tools the agent is expected to use, each with a 'name' and optional 'args'), 'expected_output' (the ideal answer or output from the agent, can include a 'rubric' for grading), and 'metadata' (any additional info). The tasks should be challenging and require multi-step reasoning, tool use, or retrieval. Here's an example of one task:
{{
  "id": "task-001",
    "input": "What is the capital of France?",
    "description": "A simple geography question testing basic knowledge.",
    "expected_tools": [],
    "expected_output": {{"answer": "Paris"}},
    "metadata": {{"difficulty": "easy", "category": "geography"}}
}}
Make sure the 'id' is unique for each task and the 'input' is clear and unambiguous. The 'expected_output' should be specific enough to allow for automated grading, and the 'description' should provide context and explain why the task is challenging. The 'expected_tools' field can be used to specify if the agent needs to use external tools (like a calculator, search engine, etc.) to solve the task. Generate tasks that are diverse in format and content, and ensure they align with the specified category."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
def parse_tasks(raw: str) -> list[Task]:
    import json
    dict_tasks = json.loads(raw)
    tasks = []
    for task in dict_tasks:
        tasks.append(Task(
            id=task["id"],
            input=task["input"],
            description=task.get("description", ""),
            expected_tools=[ExpectedTool(**tool) for tool in task.get("expected_tools", [])],
            expected_output=task.get("expected_output", {}),
            metadata=task.get("metadata", {})
        ))
    return tasks

def generate(category: Category, count: int, model: str) -> list[Task]:
    messages = build_prompt(category, count)
    raw = _chat(model, messages, temperature=0)
    tasks = parse_tasks(raw)
    tasks = [to_evalforge_yaml(t, category.name) for t in tasks]
    valid_tasks = []
    for t in tasks:
        task_obj = Task(
            id=t["id"],
            input=t["input"],
            description=t.get("description", ""),
            expected_tools=[ExpectedTool(**tool) for tool in t.get("expected_tools", [])],
            expected_output=t.get("expected_output", {}),
            metadata=t.get("metadata", {})
        )
        errors = validate(task_obj)
        if errors:
            print(f"Validation errors for task {task_obj.id}: {errors}")
        else:
            valid_tasks.append(task_obj)
    return valid_tasks


@dataclass
class Report:
    saved: int = 0
    skipped: int = 0
    per_category: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    
    def run_generation(self, category: Category, count: int, model: str):
        try:
            tasks = generate(category, count, model)
            saved = 0
            for t in tasks:
                if validate(t):
                    saved += 1
            self.saved += saved
            self.skipped += (len(tasks) - saved)
            self.per_category[category.name] = {"saved": saved, "skipped": len(tasks) - saved}
        except Exception as e:
            self.errors.append(f"Error generating for category {category.name}: {str(e)}")
            




