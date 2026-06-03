    

from dataclasses import dataclass
from evalforge.scoring.base import Score, Scorer

@dataclass
class HallucinationScorer(Scorer):
    name = "HallucinationScorer"

    def score(self, task, agent_run):
        claims = task.expected_output.get("grounded_claims", [])
        if not claims:
            return Score(name=self.name, value=1.0, details={"note": "no claims"})
        # Evidence = everything the tools actually returned.
        evidence = "\n".join(str(tc.results) for tc in agent_run.tool_calls)
        # A claim only counts if the agent asserted it in its output.
        asserted = [c for c in claims if c in agent_run.output]
        # Hallucinated = asserted but unsupported by any tool result.
        hallucinated = [c for c in asserted if c not in evidence]
        value = 1.0 if not asserted else 1.0 - len(hallucinated) / len(asserted)
        return Score(name=self.name, value=value, details={"asserted": asserted, "hallucinated": hallucinated})
    
    