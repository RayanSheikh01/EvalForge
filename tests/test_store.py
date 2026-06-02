import pytest
from evalforge.store import SCHEMA, write_jsonl, _db, upsert, persist


def test_store():
    class Rec:
        run_id = "r1"
        task_id = "t1"
        agent_name = "a1"
        ts = "2024-01-01T00:00:00Z"
        latency_ms = 123.45
        run = {"output": "hello"}
        scores = {"completion": 1.0}
        details = {"tool_calls": []}
        error = ""

    rec = Rec()
    persist(rec, out="test_results")

    # Check JSONL file
    import json
    with open("test_results/a1_t1.jsonl") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["run_id"] == "r1"
        assert data["task_id"] == "t1"

    # Check SQLite DB
    conn = _db("test_results")
    cursor = conn.execute("SELECT * FROM runs WHERE run_id=?", ("r1",))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "r1"  # run_id
    assert row[1] == "t1"  # task_id
    assert row[2] == "a1"  # agent_name
    assert row[3] == "2024-01-01T00:00:00Z"  # ts
    assert row[4] == 123.45  # latency_ms
    assert row[5] == '{"output": "hello"}'  # run
    assert row[6] == '{"completion": 1.0}'  # scores
    assert row[7] == '{"tool_calls": []}'  # details
    assert row[8] == ""  # error
    
    conn.close()
    

  