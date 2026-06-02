def trends(out="results", task=None, agent=None) -> list[dict]:
    """
    Generate a trends report for the given task and agent.

    Args:
        out: The output directory to save the report.
        task: The task to generate the report for. If None, generates for all tasks.
        agent: The agent to generate the report for. If None, generates for all agents.
        
    Returns:
        A list of dictionaries containing the trends data.
    """
    import os
    import json
    from collections import defaultdict

    # Load all runs from the output directory
    runs = []
    for filename in os.listdir(out):
        if filename.endswith(".jsonl"):
            with open(os.path.join(out, filename)) as f:
                for line in f:
                    runs.append(json.loads(line))

    # Filter runs by task and agent if specified
    if task is not None:
        runs = [r for r in runs if r["task_id"] == task]
    if agent is not None:
        runs = [r for r in runs if r["agent_name"] == agent]

    # Aggregate trends data
    trends_data = defaultdict(list)
    for run in runs:
        trends_data[run["task_id"]].append(run)

    # Convert to list of dicts for output
    report = []
    for task_id, task_runs in trends_data.items():
        report.append({
            "task_id": task_id,
            "num_runs": len(task_runs),
            "average_latency_ms": sum(r["latency_ms"] for r in task_runs) / len(task_runs),
            "average_score": sum(r["scores"].get("completion", 0) for r in task_runs) / len(task_runs),
        })

    return report

