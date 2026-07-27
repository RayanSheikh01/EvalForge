import pytest


@pytest.fixture
def db(tmp_path):
    """Return a temp directory path string to use as `out`."""
    return str(tmp_path)


def make_version(hash="abc123", name="test_prompt", parent=None,
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
