import pytest


def test_judge(monkeypatch):
    from evalforge.scoring import judge
    from evalforge.scoring.judge import JudgeScorer

    monkeypatch.setattr(judge, "_chat", lambda model, messages: "0.9")

    scorer = JudgeScorer()
    task = type("Task", (), {"input": "What is 2 + 2?"})()
    agent_run = type("AgentRun", (), {"output": "2 + 2 is 4."})()
    score = scorer.score(task, agent_run)
    assert 0.0 <= score.value <= 1.0, f"Score value should be between 0 and 1, got {score.value}"
