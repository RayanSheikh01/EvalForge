from evalforge.prompts.store import *
from datetime import datetime
import os
import hashlib

def compute_hash(content: str) -> str:
    """
    Return the first 12 characters of the SHA256 hash of the content string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

def init_prompt(filepath: str, out: str = "results") -> dict:
    """
    Start tracking a prompt file.
    - Read the file content
    - Compute hash
    - Derive prompt_name from the filename (stem, no extension)
    - Create the first version (parent_hash=None)
    - Set it as active
    - Return the version dict
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    hash = compute_hash(content)
    prompt_name = os.path.splitext(os.path.basename(filepath))[0]
    insert_version({
        "hash": hash,
        "name": prompt_name,
        "parent_hash": None,
        "message": "",
        "author": "",
        "timestamp": datetime.now().isoformat(),
        "content": content,
        "tags": "[]",
    }, out)
    set_active(prompt_name, hash, out)
    return {
        "hash": hash,
        "name": prompt_name,
        "parent_hash": None,
        "message": "",
        "author": "",
        "timestamp": datetime.now().isoformat(),
        "content": content,
        "tags": "[]",
    }    

def commit_prompt(prompt_name: str, filepath: str, message: str = "", out: str = "results") -> dict:
    """
    Snapshot the current file content as a new version.
    - Read the file content
    - Compute hash
    - If hash == current active hash, raise/warn (no changes)
    - Look up current active hash as parent_hash
    - Insert new version
    - Update active pointer
    - Return the version dict
    """
    active_hash = get_active(prompt_name, out)
    if active_hash is None:
        raise ValueError(f"Prompt '{prompt_name}' is not tracked.")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    hash = compute_hash(content)
    if hash == active_hash:
        raise ValueError(f"No changes detected for prompt '{prompt_name}'.")
    insert_version({
        "hash": hash,
        "name": prompt_name,
        "parent_hash": active_hash,
        "message": message,
        "author": "",
        "timestamp": datetime.now().isoformat(),
        "content": content,
        "tags": "[]",
    }, out)
    set_active(prompt_name, hash, out)
    return {
        "hash": hash,
        "name": prompt_name,
        "parent_hash": active_hash,
        "message": message,
        "author": "",
        "timestamp": datetime.now().isoformat(),
        "content": content,
        "tags": "[]",
    }    
    
def log_prompt(prompt_name: str, limit: int = 20, out: str = "results") -> list[dict]:
    """
    Return version history for a prompt (delegates to store.get_history).
    """
    return get_history(prompt_name, out)

def show_version(hash: str, out: str = "results") -> str:
    """
    Return the prompt content at a specific version hash.
    """
    return get_version(hash, out)["content"]

def rollback_prompt(prompt_name: str, target_hash: str, message: str = "", out: str = "results") -> None:
    """
    Restore a prompt to a previous version by setting the active pointer.
    """
    target_version = get_version(target_hash, out)
    if target_version is None:
        raise ValueError(f"Version '{target_hash}' not found for prompt '{prompt_name}'.")
    set_active(prompt_name, target_hash, out)

def list_tracked(out: str = "results") -> list[dict]:
    """
    Return all tracked prompts.
    """
    return list_prompts(out)


def get_active_content(prompt_name: str, out: str = "results") -> str:
    """
    Convenience: return the content of the currently active version.
    """
    return get_version(get_active(prompt_name, out), out)["content"]

def best_version(prompt_name: str, metric: str = "completion", out: str = "results") -> dict | None:
    """
    Query all runs linked to this prompt's versions.
    Group by prompt_version, average the given metric.
    Return the version dict with the highest average.
    """
    conn = connect(out)
    c = conn.cursor()
    c.execute(
        """
        SELECT v.hash, v.prompt_name, v.parent_hash, v.message,
               v.author, v.timestamp, v.content, v.tags,
               AVG(r.completion_score) AS avg_completion,
               AVG(r.fluency_score) AS avg_fluency,
               AVG(r.usefulness_score) AS avg_usefulness
        FROM prompt_versions v
        LEFT JOIN runs r ON v.hash = r.prompt_version
        WHERE v.name = ?
        GROUP BY v.hash, v.prompt_name, v.parent_hash, v.message,
                 v.author, v.timestamp, v.content, v.tags
        ORDER BY avg_completion DESC
        LIMIT 1
        """,
        (prompt_name,),
    )
    row = c.fetchone()
    if not row:
        return None
    col_names = [d[0] for d in c.description]
    return dict(zip(col_names, row))
    