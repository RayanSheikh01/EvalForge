import os
import sqlite3


COLUMNS = ["hash", "name", "parent_hash", "message", "author",
           "timestamp", "content", "tags"]


def connect(out: str = "results") -> sqlite3.Connection:
    """Open (or create) prompts.db, ensure tables exist, return connection."""
    os.makedirs(out, exist_ok=True)
    conn = sqlite3.connect(os.path.join(out, "prompts.db"))
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute(
        "CREATE TABLE IF NOT EXISTS prompt_versions ("
        "  hash TEXT PRIMARY KEY,"
        "  name TEXT NOT NULL,"
        "  parent_hash TEXT,"
        "  message TEXT NOT NULL DEFAULT '',"
        "  author TEXT NOT NULL DEFAULT '',"
        "  timestamp TEXT NOT NULL,"
        "  content TEXT NOT NULL,"
        "  tags TEXT DEFAULT '[]'"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS prompt_active ("
        "  name TEXT PRIMARY KEY,"
        "  active_hash TEXT NOT NULL,"
        "  FOREIGN KEY (active_hash) REFERENCES prompt_versions(hash)"
        ")"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_versions_name "
        "ON prompt_versions(name)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_versions_ts "
        "ON prompt_versions(timestamp)"
    )
    conn.commit()
    return conn


def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row) if row else None


def insert_version(version: dict, out: str = "results") -> None:
    """INSERT a version record into prompt_versions."""
    conn = connect(out)
    conn.execute(
        "INSERT INTO prompt_versions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        tuple(version[col] for col in COLUMNS),
    )
    conn.commit()
    conn.close()


def set_active(prompt_name: str, hash: str, out: str = "results") -> None:
    """INSERT OR REPLACE into prompt_active."""
    conn = connect(out)
    conn.execute(
        "INSERT OR REPLACE INTO prompt_active VALUES (?, ?)",
        (prompt_name, hash),
    )
    conn.commit()
    conn.close()


def get_active(prompt_name: str, out: str = "results") -> str | None:
    """Return the active hash for a prompt, or None."""
    conn = connect(out)
    row = conn.execute(
        "SELECT active_hash FROM prompt_active WHERE name = ?",
        (prompt_name,),
    ).fetchone()
    conn.close()
    return row["active_hash"] if row else None


def get_version(hash: str, out: str = "results") -> dict | None:
    """Return a single version row as a dict, or None."""
    conn = connect(out)
    row = conn.execute(
        "SELECT * FROM prompt_versions WHERE hash = ?", (hash,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_history(prompt_name: str, out: str = "results") -> list[dict]:
    """Return all versions for a prompt, ordered by timestamp descending."""
    conn = connect(out)
    rows = conn.execute(
        "SELECT * FROM prompt_versions WHERE name = ? "
        "ORDER BY timestamp DESC",
        (prompt_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_prompts(out: str = "results") -> list[dict]:
    """Return all tracked prompts with their active hash."""
    conn = connect(out)
    rows = conn.execute("SELECT * FROM prompt_active").fetchall()
    conn.close()
    return [dict(r) for r in rows]