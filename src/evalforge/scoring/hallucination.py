    

from dataclasses import dataclass
from evalforge.scoring.base import Score, Scorer

@dataclass
class HallucinationScorer(Scorer):
    name = "HallucinationScorer"

    def score(self, task, agent_run):
        claims = task.expected_output.get("grounded_claims", [])
        if not claims:
            return Score(name=self.name, value=1.0, details={"reason": "No grounded claims provided"})
        hallucinated_claims = [claim for claim in claims if claim not in agent_run.output]
        hallucination_rate = len(hallucinated_claims) / len(claims)
        return Score(name=self.name, value=1 - hallucination_rate, details={"hallucinated_claims": hallucinated_claims})
    
    