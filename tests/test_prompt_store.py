from evalforge.prompts.diff import diff_versions
from evalforge.prompts.vault import *
import os
import pytest
from evalforge.prompts.store import *


@pytest.fixture
def db(tmp_path):
    """Return a temp directory path string to use as `out`."""
    return str(tmp_path)


def _make_version(hash="abc123", name="test_prompt", parent=None,
                  message="initial", content="You are helpful."):
    return {
        "hash": hash,
        "name": name,
        "parent_hash": parent,
        "message": message,
        "author": "tester",
        "timestamp": "2026-07-27T12:00:00Z",
        "content": content,
        "tags": "[]",
    }


def test_connect_creates_db_file(db):
    conn = connect(db)
    conn.close()
    assert os.path.exists(os.path.join(db, "prompts.db"))


def test_connect_creates_directory_if_missing(tmp_path):
    nested = str(tmp_path / "deep" / "nested")
    conn = connect(nested)
    conn.close()
    assert os.path.exists(os.path.join(nested, "prompts.db"))


def test_insert_and_retrieve(db):
    v = _make_version()
    insert_version(v, db)
    result = get_version("abc123", db)
    assert result is not None
    assert result["hash"] == "abc123"
    assert result["name"] == "test_prompt"
    assert result["content"] == "You are helpful."


def test_get_version_returns_none_for_missing_hash(db):
    connect(db).close()
    assert get_version("nonexistent", db) is None


def test_set_and_get_active(db):
    v = _make_version()
    insert_version(v, db)
    set_active("test_prompt", "abc123", db)
    assert get_active("test_prompt", db) == "abc123"


def test_get_active_returns_none_when_not_set(db):
    connect(db).close()
    assert get_active("unknown", db) is None


def test_replace_active(db):
    v1 = _make_version(hash="aaa", content="v1")
    v2 = _make_version(hash="bbb", content="v2")
    insert_version(v1, db)
    insert_version(v2, db)
    set_active("test_prompt", "aaa", db)
    assert get_active("test_prompt", db) == "aaa"
    set_active("test_prompt", "bbb", db)
    assert get_active("test_prompt", db) == "bbb"


def test_history_ordering_descending_by_timestamp(db):
    for i, ts in enumerate(["2026-01-01", "2026-06-15", "2026-12-31"]):
        v = _make_version(hash=f"h{i}", message=f"v{i}")
        v["timestamp"] = ts
        insert_version(v, db)
    history = get_history("test_prompt", db)
    assert len(history) == 3
    assert history[0]["timestamp"] == "2026-12-31"
    assert history[2]["timestamp"] == "2026-01-01"


def test_history_empty_for_unknown_prompt(db):
    connect(db).close()
    assert get_history("ghost", db) == []


def test_list_prompts_lists_tracked(db):
    v1 = _make_version(hash="h1", name="prompt_a")
    v2 = _make_version(hash="h2", name="prompt_b")
    insert_version(v1, db)
    insert_version(v2, db)
    set_active("prompt_a", "h1", db)
    set_active("prompt_b", "h2", db)
    prompts = list_prompts(db)
    names = {p["name"] for p in prompts}
    assert names == {"prompt_a", "prompt_b"}


def test_list_prompts_empty_when_none_tracked(db):
    connect(db).close()
    assert list_prompts(db) == []



def test_compute_hash_is_12_chars():
    h = compute_hash("hello world")
    assert len(h) == 12
    assert all(c in "0123456789abcdef" for c in h)


def test_compute_hash_deterministic():
    assert compute_hash("same") == compute_hash("same")


def test_compute_hash_different_for_different_content():
    assert compute_hash("aaa") != compute_hash("bbb")


def test_init_prompt(db, tmp_path):
    f = tmp_path / "greet.txt"
    f.write_text("Hello!", encoding="utf-8")
    v = init_prompt(str(f), out=db)
    assert v["name"] == "greet"
    assert v["content"] == "Hello!"
    assert v["parent_hash"] is None
    assert get_active("greet", db) == v["hash"]


def test_init_prompt_hash_matches_content(db, tmp_path):
    f = tmp_path / "p.txt"
    f.write_text("test content", encoding="utf-8")
    v = init_prompt(str(f), out=db)
    assert v["hash"] == compute_hash("test content")


def test_commit_prompt_creates_new_version(db, tmp_path):
    f = tmp_path / "agent.txt"
    f.write_text("v1", encoding="utf-8")
    init_prompt(str(f), out=db)

    f.write_text("v2", encoding="utf-8")
    v2 = commit_prompt("agent", str(f), message="update", out=db)
    assert v2["content"] == "v2"
    assert v2["parent_hash"] == compute_hash("v1")
    assert get_active("agent", db) == v2["hash"]


def test_commit_prompt_raises_when_untracked(db, tmp_path):
    f = tmp_path / "unknown.txt"
    f.write_text("x", encoding="utf-8")
    connect(db).close()
    with pytest.raises(ValueError, match="not tracked"):
        commit_prompt("unknown", str(f), out=db)


def test_commit_prompt_raises_on_no_changes(db, tmp_path):
    f = tmp_path / "same.txt"
    f.write_text("unchanged", encoding="utf-8")
    init_prompt(str(f), out=db)
    with pytest.raises(ValueError, match="No changes"):
        commit_prompt("same", str(f), out=db)


def test_log_prompt_returns_history(db, tmp_path):
    f = tmp_path / "log_test.txt"
    f.write_text("first", encoding="utf-8")
    init_prompt(str(f), out=db)
    f.write_text("second", encoding="utf-8")
    commit_prompt("log_test", str(f), out=db)
    history = log_prompt("log_test", out=db)
    assert len(history) == 2


def test_show_version_returns_content(db, tmp_path):
    f = tmp_path / "show.txt"
    f.write_text("my content", encoding="utf-8")
    v = init_prompt(str(f), out=db)
    assert show_version(v["hash"], out=db) == "my content"


def test_rollback_prompt_restores_old_version(db, tmp_path):
    f = tmp_path / "roll.txt"
    f.write_text("original", encoding="utf-8")
    v1 = init_prompt(str(f), out=db)

    f.write_text("changed", encoding="utf-8")
    commit_prompt("roll", str(f), out=db)

    rollback_prompt("roll", v1["hash"], out=db)
    assert get_active_content("roll", out=db) == "original"


def test_rollback_prompt_raises_for_bad_hash(db, tmp_path):
    f = tmp_path / "rb.txt"
    f.write_text("x", encoding="utf-8")
    init_prompt(str(f), out=db)
    with pytest.raises(ValueError, match="not found"):
        rollback_prompt("rb", "badhash12345", out=db)


def test_list_tracked_returns_all(db, tmp_path):
    for name in ["alpha", "beta"]:
        f = tmp_path / f"{name}.txt"
        f.write_text(f"{name} content", encoding="utf-8")
        init_prompt(str(f), out=db)
    tracked = list_tracked(out=db)
    names = {p["name"] for p in tracked}
    assert names == {"alpha", "beta"}


def test_get_active_content(db, tmp_path):
    f = tmp_path / "active.txt"
    f.write_text("live content", encoding="utf-8")
    init_prompt(str(f), out=db)
    assert get_active_content("active", out=db) == "live content"


def test_full_workflow_init_commit_log_rollback(db, tmp_path):
    """End-to-end: init → commit → verify log → rollback → verify active."""
    f = tmp_path / "workflow.txt"
    f.write_text("v1", encoding="utf-8")
    v1 = init_prompt(str(f), out=db)

    f.write_text("v2", encoding="utf-8")
    v2 = commit_prompt("workflow", str(f), message="bump", out=db)

    history = log_prompt("workflow", out=db)
    assert len(history) == 2

    rollback_prompt("workflow", v1["hash"], out=db)
    assert get_active_content("workflow", out=db) == "v1"


def test_diff_shows_additions(db, tmp_path):
    f = tmp_path / "d.txt"
    f.write_text("hello", encoding="utf-8")
    v1 = init_prompt(str(f), out=db)
    f.write_text("hello\nworld", encoding="utf-8")
    v2 = commit_prompt("d", str(f), out=db)
    result = diff_versions(v1["content"], v2["content"])
    assert "+world" in result


def test_diff_identical_empty(db, tmp_path):
    f = tmp_path / "eq.txt"
    f.write_text("same content", encoding="utf-8")
    v = init_prompt(str(f), out=db)
    result = diff_versions(v["content"], v["content"])
    assert result == ""