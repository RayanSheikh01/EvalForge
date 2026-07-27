import pytest
from evalforge.prompts.vault import *
from evalforge.prompts.store import connect, get_active


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
    """End-to-end: init -> commit -> verify log -> rollback -> verify active."""
    f = tmp_path / "workflow.txt"
    f.write_text("v1", encoding="utf-8")
    v1 = init_prompt(str(f), out=db)

    f.write_text("v2", encoding="utf-8")
    v2 = commit_prompt("workflow", str(f), message="bump", out=db)

    history = log_prompt("workflow", out=db)
    assert len(history) == 2

    rollback_prompt("workflow", v1["hash"], out=db)
    assert get_active_content("workflow", out=db) == "v1"
