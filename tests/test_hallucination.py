import pytest

from evalforge.scoring import hallucination
from evalforge.scoring.hallucination import HallucinationScorer

def test_hallucination(monkeypatch):

    scorer = HallucinationScorer()
    task = type("Task", (), {"expected_output": {"grounded_claims": ["Claim A", "Claim B"]}})()
    agent_run = type("AgentRun", (), {"output": "Claim A"})()
    score = scorer.score(task, agent_run)
    assert 0.0 <= score.value <= 1.0, f"Score value should be between 0 and 1, got {score.value}"
    assert score.details["hallucinated_claims"] == ["Claim B"], f"Expected hallucinated claims to be ['Claim B'], got {score.details['hallucinated_claims']}"
    
    # Test case with no grounded claims
    task_no_claims = type("Task", (), {"expected_output": {"grounded_claims": []}})()
    score_no_claims = scorer.score(task_no_claims, agent_run)
    assert score_no_claims.value == 1.0, f"Expected score to be 1.0 when no grounded claims are provided, got {score_no_claims.value}"
    assert score_no_claims.details["reason"] == "No grounded claims provided", f"Expected reason to be 'No grounded claims provided', got {score_no_claims.details['reason']}"
    