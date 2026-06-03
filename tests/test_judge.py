from evalforge.scoring import judge
from evalforge.scoring.judge import JudgeScorer


def _task(expected_output):
    return type("Task", (), {"input": "What is 2 + 2?", "expected_output": expected_output})()


def _run(output="2 + 2 is 4."):
    return type("AgentRun", (), {"output": output})()


def test_no_rubric_returns_one(monkeypatch):
    # Never touches Ollama when there is no rubric.
    monkeypatch.setattr(judge, "_chat", lambda model, messages: (_ for _ in ()).throw(AssertionError))
    score = JudgeScorer().score(_task({}), _run())
    assert score.value == 1.0
    assert score.details["note"] == "no rubric"


def test_valid_json_score(monkeypatch):
    monkeypatch.setattr(judge, "_chat", lambda model, messages: '{"score": 0.8, "reason": "ok"}')
    score = JudgeScorer().score(_task({"rubric": "grade it"}), _run())
    assert score.value == 0.8
    assert score.details["reason"] == "ok"


def test_chat_raises_degrades_to_zero(monkeypatch):
    def boom(model, messages):
        raise RuntimeError("connection refused")
    monkeypatch.setattr(judge, "_chat", boom)
    score = JudgeScorer().score(_task({"rubric": "grade it"}), _run())
    assert score.value == 0.0
    assert "error" in score.details


def test_score_clamped_to_one(monkeypatch):
    monkeypatch.setattr(judge, "_chat", lambda model, messages: '{"score": 1.5, "reason": "too high"}')
    score = JudgeScorer().score(_task({"rubric": "grade it"}), _run())
    assert score.value == 1.0
