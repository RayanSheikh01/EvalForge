import json
import os
import sqlite3


def trends(out="results", task=None, agent=None, prompt_version=None) -> list[dict]:
    """Return stored runs as dicts, ordered by (task_id, agent_name, ts).

    Reads the SQLite ``runs`` table written by the store. The ``scores`` column
    (JSON text) is expanded into a dict so callers can read per-run metrics
    (e.g. completion) directly. Delta between consecutive runs is computed by
    the caller.
    """
    db_path = os.path.join(out, "results.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    sql = "SELECT * FROM runs WHERE 1=1"
    params = []
    if task is not None:
        sql += " AND task_id = ?"
        params.append(task)
    if agent is not None:
        sql += " AND agent_name = ?"
        params.append(agent)
    if prompt_version is not None:
        sql += " AND prompt_version = ?"
        params.append(prompt_version)
    sql += " ORDER BY task_id, agent_name, ts"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        try:
            d["scores"] = json.loads(d["scores"]) if d.get("scores") else {}
        except (TypeError, json.JSONDecodeError):
            d["scores"] = {}
        result.append(d)
    return result
