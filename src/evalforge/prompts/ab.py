from evalforge.prompts.diff import diff_versions
from evalforge.task import load_tasks
from evalforge.cli import _load_agent
from evalforge.store import persist
from evalforge.runner import run_suite
from evalforge.prompts.store import get_active_content

def run_ab(agent_spec: str, prompt_a: str, prompt_b: str,
           tasks_path: str, out: str = "results") -> dict:
     """
    Run the full task suite twice — once per prompt version.
    
    1. Resolve prompt_a and prompt_b to their active hashes (or treat as hashes directly)
    2. Load tasks
    3. Instantiate agent with prompt A content, run suite, collect records
    4. Instantiate agent with prompt B content, run suite, collect records
    5. Persist all records (each tagged with its prompt_version)
    6. Return a comparison dict:
       {
         task_id: {
           metric: { "a": score, "b": score, "delta": score_b - score_a }
         }
       }
    """
    agent = _load_agent(agent_spec)
    tasks = load_tasks(tasks_path)
    hash_a = get_active_content(prompt_a, out)
    hash_b = get_active_content(prompt_b, out)
    
    recs_a = run_suite(agent, tasks, hash_a, out)
    recs_b = run_suite(agent, tasks, hash_b, out)
    
    for rec in recs_a:
        persist(rec, out, hash_a)
    for rec in recs_b:
        persist(rec, out, hash_b)
    
    return diff_versions(hash_a, hash_b, out)


def format_comparison(comparison: dict) -> str:
    for task_id, metrics in comparison.items():
        print(f"Task: {task_id}")
        for metric, scores in metrics.items():
            print(f"  {metric}: {scores['a']} vs {scores['b']} (delta: {scores['delta']})")