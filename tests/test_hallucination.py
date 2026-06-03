from evalforge.agent import AgentRun, ToolCall, TokenUsage
from evalforge.scoring.hallucination import HallucinationScorer


def _run(output, results=None):
    return AgentRun(
        output=output,
        tool_calls=[ToolCall("web_search", {"query": "q"}, results=results)],
        token_usage=TokenUsage(),
    )


def _task(claims):
    return type("Task", (), {"expected_output": {"grounded_claims": claims}})()


def test_no_claims_is_one():
    score = HallucinationScorer().score(_task([]), _run("anything"))
    assert score.value == 1.0
    assert score.details["note"] == "no claims"


def test_asserted_claim_in_evidence_is_grounded():
    # Claim is in the output AND backed by a tool result -> not hallucinated.
    run = _run("The sky is blue", results="the sky is blue per sensor")
    score = HallucinationScorer().score(_task(["sky is blue"]), run)
    assert score.value == 1.0
    assert score.details["hallucinated"] == []


def test_asserted_claim_absent_from_evidence_is_hallucinated():
    # Claim asserted in output but no tool result supports it -> hallucinated.
    run = _run("The sky is green", results="unrelated data")
    score = HallucinationScorer().score(_task(["sky is green"]), run)
    assert score.value < 1.0
    assert "sky is green" in score.details["hallucinated"]


def test_claim_not_in_output_is_ignored():
    # Agent never made the claim -> not counted, score stays 1.0.
    run = _run("totally different text", results="nothing relevant")
    score = HallucinationScorer().score(_task(["sky is blue"]), run)
    assert score.value == 1.0
    assert score.details["asserted"] == []
