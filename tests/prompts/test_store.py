import os
from evalforge.prompts.store import *
from tests.prompts.conftest import make_version


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
    v = make_version()
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
    v = make_version()
    insert_version(v, db)
    set_active("test_prompt", "abc123", db)
    assert get_active("test_prompt", db) == "abc123"


def test_get_active_returns_none_when_not_set(db):
    connect(db).close()
    assert get_active("unknown", db) is None


def test_replace_active(db):
    v1 = make_version(hash="aaa", content="v1")
    v2 = make_version(hash="bbb", content="v2")
    insert_version(v1, db)
    insert_version(v2, db)
    set_active("test_prompt", "aaa", db)
    assert get_active("test_prompt", db) == "aaa"
    set_active("test_prompt", "bbb", db)
    assert get_active("test_prompt", db) == "bbb"


def test_history_ordering_descending_by_timestamp(db):
    for i, ts in enumerate(["2026-01-01", "2026-06-15", "2026-12-31"]):
        v = make_version(hash=f"h{i}", message=f"v{i}")
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
    v1 = make_version(hash="h1", name="prompt_a")
    v2 = make_version(hash="h2", name="prompt_b")
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
