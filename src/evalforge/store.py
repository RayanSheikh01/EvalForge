import json
import os
import sqlite3
from dataclasses import asdict, is_dataclass

FIELDS = [
    "run_id",
    "task_id",
    "agent_name",
    "ts",
    "latency_ms",
    "run",
    "scores",
    "details",
    "error",
    "prompt_version",
]


def _to_dict(rec):
    """Pull RunRecord fields into a plain dict. Works for dataclass records
    and plain objects; nested dataclasses (AgentRun, ToolCall) are expanded."""
    out = {}
    for k in FIELDS:
        v = getattr(rec, k)
        out[k] = asdict(v) if is_dataclass(v) else v
    return out


def write_jsonl(rec, out="results"):
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, f"{rec.agent_name}_{rec.task_id}.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(_to_dict(rec), default=str) + "\n")


SCHEMA = """CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    task_id TEXT,
    agent_name TEXT,
    ts TEXT,
    latency_ms REAL,
    run TEXT,
    scores TEXT,
    details TEXT,
    error TEXT,
    prompt_version TEXT DEFAULT '',
)"""


def _db(out):
    os.makedirs(out, exist_ok=True)
    conn = sqlite3.connect(os.path.join(out, "results.db"))
    conn.execute(SCHEMA)
    return conn


def upsert(rec, out):
    conn = _db(out)
    d = _to_dict(rec)
    conn.execute(
        "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?)",
        (
            d["run_id"],
            d["task_id"],
            d["agent_name"],
            d["ts"],
            d["latency_ms"],
            json.dumps(d["run"], default=str),
            json.dumps(d["scores"], default=str),
            json.dumps(d["details"], default=str),
            d["error"],
            d["prompt_version"],
        ),
    )
    conn.commit()
    conn.close()


def persist(rec, out="results"):
    write_jsonl(rec, out)
    upsert(rec, out)
