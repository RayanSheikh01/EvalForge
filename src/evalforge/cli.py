from evalforge.prompts.vault import get_active_content
import argparse
from evalforge.prompts.store import list_prompts, set_active, get_active, get_version
from evalforge.prompts.vault import commit_prompt, init_prompt, rollback_prompt, log_prompt
from evalforge.prompts.diff import diff_versions
import argparse
import importlib
import os
import sys

from evalforge.task import load_tasks
from evalforge.runner import run_suite
from evalforge.store import persist
from evalforge.report import trends

# The root-level `generator/` package resolves the same way `adapters/` does:
# CWD is not on sys.path under console scripts / uv run, so add it before import.
_cwd = os.getcwd()
if _cwd not in sys.path:
    sys.path.insert(0, _cwd)

from generator import run_generation, CATEGORIES, all_categories


def _load_agent(spec):
    """spec is "module.path:ClassName" — import and instantiate."""
    module_name, _, cls_name = spec.partition(":")
    if not cls_name:
        raise ValueError(f"Agent spec must be 'module:ClassName', got: {spec!r}")
    # Resolve repo-root adapters (e.g. "adapters.example_echo") when invoked
    # from the repo root — CWD is not on sys.path under console scripts / uv run.
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    mod = importlib.import_module(module_name)
    return getattr(mod, cls_name)()





def cmd_report(a):
    rows = trends(out=a.out, task=a.task, agent=a.agent)
    prev = {}
    for row in rows:
        key = (row["task_id"], row["agent_name"])
        completion = row["scores"].get("completion", 0.0)
        last = prev.get(key)
        delta = "" if last is None else f" delta={completion - last:+.2f}"
        print(
            f"{row['task_id']} [{row['agent_name']}] {row['ts']}: "
            f"completion={completion:.2f} "
            f"latency_ms={row['latency_ms']:.1f}"
            f"{delta}"
        )
        prev[key] = completion
    
def cmd_generate(a):
    cats = all_categories() if a.all else [CATEGORIES[a.category]]
    report = run_generation(cats, a.count, a.dry_run, a.out)
    for key, counts in report.per_category.items():
        print(f"  {key}: {counts['saved']} saved, {counts['skipped']} skipped")
    print(f"Generated: {report.saved} saved, {report.skipped} skipped")


def cmd_run(a):
    agent = _load_agent(a.agent)
    # `--tasks all` means the whole tasks/ tree (recursive load picks up subdirs).
    tasks_path = "tasks" if a.tasks == "all" else a.tasks
    tasks = load_tasks(tasks_path)
    if a.prompt:
        prompt = get_active_content(a.prompt, a.out)
    records = run_suite(agent, tasks, prompt)
    for rec in records:
        persist(rec, a.out, prompt)
        s = rec.scores
        print(
            f"{rec.task_id}: "
            f"completion={s.get('completion', 0):.2f} "
            f"tool_accuracy={s.get('tool_accuracy', 0):.2f} "
            f"latency_ms={s.get('latency', 0):.1f} "
            f"cost_usd={s.get('token_cost', 0)}"
        )



def cmd_prompt(a):
    parser = argparse.ArgumentParser(description="Prompt management")
    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.add_parser("log", help="Log of a prompt")
    subparsers.add_parser("show", help="Show a version of a prompt")
    subparsers.add_parser("diff", help="Diff between two versions of a prompt")
    subparsers.add_parser("rollback", help="Rollback a prompt to a version")
    subparsers.add_parser("init", help="Initialize a prompt")
    subparsers.add_parser("commit", help="Commit a prompt")
    subparsers.add_parser("active", help="Get the active version of a prompt")
    subparsers.add_parser("set-active", help="Set the active version of a prompt")
    subparsers.add_parser("list", help="List all prompts")
    subparsers.add_parser("set-active-content", help="Set the active content of a prompt")


    if a.subcommand == "log":
        for h in log_prompt(a.name, out=a.out):
            print(h["hash"])
    elif a.subcommand == "show":
        v = get_version(a.hash, out=a.out)
        print(v["content"])
    elif a.subcommand == "diff":
        print(diff_versions(a.hash1, a.hash2, out=a.out))
    elif a.subcommand == "rollback":
        rollback_prompt(a.name, a.hash, out=a.out)
    elif a.subcommand == "init":
        v = init_prompt(a.file, out=a.out)
        print(v["hash"])
    elif a.subcommand == "commit":
        v = commit_prompt(a.name, a.file, message=a.message, out=a.out)
        print(v["hash"])
    elif a.subcommand == "active":
        print(get_active(a.name, out=a.out))
    elif a.subcommand == "set-active":
        set_active(a.name, a.hash, out=a.out)
    elif a.subcommand == "list":
        for p in list_prompts(out=a.out):
            print(p["name"])
    else:
        parser.print_help()



def main():
    parser = argparse.ArgumentParser(description="EvalForge CLI")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run an agent over a task suite")
    run_parser.add_argument("--tasks", required=True, help="Task file or directory")
    run_parser.add_argument("--agent", required=True, help="Agent spec 'module:ClassName'")
    run_parser.add_argument("--out", default="results", help="Output directory")
    run_parser.add_argument("--prompt", default="", help="Prompt name")
    run_parser.set_defaults(fn=cmd_run)

    report_parser = subparsers.add_parser("report", help="Show scored trends")
    report_parser.add_argument("--task", default=None, help="Filter by task id")
    report_parser.add_argument("--agent", default=None, help="Filter by agent name")
    report_parser.add_argument("--out", default="results", help="Output directory")
    report_parser.set_defaults(fn=cmd_report)

    gen_parser = subparsers.add_parser("generate", help="Generate adversarial tasks")
    gen_target = gen_parser.add_mutually_exclusive_group(required=True)
    gen_target.add_argument("--category", choices=list(CATEGORIES), help="One category")
    gen_target.add_argument("--all", action="store_true", help="All categories")
    gen_parser.add_argument("--count", type=int, default=5, help="Tasks per category")
    gen_parser.add_argument("--dry-run", action="store_true", help="Print, do not write")
    gen_parser.add_argument("--out", default="tasks/generated", help="Output directory")
    gen_parser.set_defaults(fn=cmd_generate)

    args = parser.parse_args()
    if getattr(args, "fn", None):
        args.fn(args)
    else:
        parser.print_help()
