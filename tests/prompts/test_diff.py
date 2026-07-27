from evalforge.prompts.diff import diff_versions
from evalforge.prompts.vault import init_prompt, commit_prompt


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
