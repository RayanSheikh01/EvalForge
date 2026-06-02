def _load_agent(spec):
    if spec == "echo":
        from adapters.example_echo import echo_agent
        return echo_agent
    raise ValueError(f"Unknown agent spec: {spec}")

def cmd_run(a):
    agent = _load_agent(a.agent)
    print(f"Running agent {agent.name} with input: {a.input}")
    run_record = agent.run(a.input)
    print(f"Output: {run_record.output}")
    print(f"Tool calls: {run_record.tool_calls}")
    # write file
    output = getattr(a, "output", None) or "run_record.json"
    with open(output, "w") as f:
        import json
        json.dump(run_record.__dict__, f, default=str)
    

def cmd_report(a):
    trends = ["completion", "tool_accuracy", "latency", "token_cost"]
    print(f"Generating report for trends: {trends}")
    report = trends(out=a.output, task=a.task, agent=a.agent)
    for entry in report:
        print(entry)
        
def main(**kwargs):
    import argparse

    parser = argparse.ArgumentParser(description="EvalForge CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run an agent on a task")
    run_parser.add_argument("--agent", required=True, help="Agent spec to run")
    run_parser.add_argument("--input", required=True, help="Input for the agent")
    run_parser.add_argument("--output", default="run_record.json", help="Output file for the run record")

    report_parser = subparsers.add_parser("report", help="Generate a report")
    report_parser.add_argument("--output", required=True, help="Output file for the report")
    report_parser.add_argument("--task", required=True, help="Task spec for the report")
    report_parser.add_argument("--agent", required=True, help="Agent spec for the report")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "report":
        cmd_report(args)
    else:
        parser.print_help()