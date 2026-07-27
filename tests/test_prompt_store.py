"""Tests for src/evalforge/prompts/store.py — Phase 1 verification."""

import os
import pytest
from evalforge.prompts.store import (
    connect,
    insert_version,
    set_active,
    get_active,
    get_version,
    get_history,
    list_prompts,
)


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


class TestConnect:
    def test_creates_db_file(self, db):
        conn = connect(db)
        conn.close()
        assert os.path.exists(os.path.join(db, "prompts.db"))

    def test_creates_directory_if_missing(self, tmp_path):
        nested = str(tmp_path / "deep" / "nested")
        conn = connect(nested)
        conn.close()
        assert os.path.exists(os.path.join(nested, "prompts.db"))


class TestInsertAndGetVersion:
    def test_insert_and_retrieve(self, db):
        v = _make_version()
        insert_version(v, db)
        result = get_version("abc123", db)
        assert result is not None
        assert result["hash"] == "abc123"
        assert result["name"] == "test_prompt"
        assert result["content"] == "You are helpful."

    def test_returns_none_for_missing_hash(self, db):
        connect(db).close()  # ensure db exists
        assert get_version("nonexistent", db) is None


class TestSetAndGetActive:
    def test_set_and_get(self, db):
        v = _make_version()
        insert_version(v, db)
        set_active("test_prompt", "abc123", db)
        assert get_active("test_prompt", db) == "abc123"

    def test_returns_none_when_not_set(self, db):
        connect(db).close()
        assert get_active("unknown", db) is None

    def test_replace_active(self, db):
        v1 = _make_version(hash="aaa", content="v1")
        v2 = _make_version(hash="bbb", content="v2")
        insert_version(v1, db)
        insert_version(v2, db)
        set_active("test_prompt", "aaa", db)
        assert get_active("test_prompt", db) == "aaa"
        set_active("test_prompt", "bbb", db)
        assert get_active("test_prompt", db) == "bbb"


class TestGetHistory:
    def test_ordering_descending_by_timestamp(self, db):
        for i, ts in enumerate(["2026-01-01", "2026-06-15", "2026-12-31"]):
            v = _make_version(hash=f"h{i}", message=f"v{i}")
            v["timestamp"] = ts
            insert_version(v, db)
        history = get_history("test_prompt", db)
        assert len(history) == 3
        assert history[0]["timestamp"] == "2026-12-31"
        assert history[2]["timestamp"] == "2026-01-01"

    def test_empty_for_unknown_prompt(self, db):
        connect(db).close()
        assert get_history("ghost", db) == []


class TestListPrompts:
    def test_lists_tracked_prompts(self, db):
        v1 = _make_version(hash="h1", name="prompt_a")
        v2 = _make_version(hash="h2", name="prompt_b")
        insert_version(v1, db)
        insert_version(v2, db)
        set_active("prompt_a", "h1", db)
        set_active("prompt_b", "h2", db)
        prompts = list_prompts(db)
        names = {p["name"] for p in prompts}
        assert names == {"prompt_a", "prompt_b"}

    def test_empty_when_none_tracked(self, db):
        connect(db).close()
        assert list_prompts(db) == []
