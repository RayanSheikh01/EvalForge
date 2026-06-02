from dataclasses import dataclass

from evalforge.scoring.base import Score, Scorer

@dataclass
class LatencyScorer(Scorer):
    name = "LatencyScorer"

    def score(self, task, agent_run) -> Score:
        latency = agent_run.latency_ms
        # Convert latency to a score between 0 and 1 (lower is better)
        value = max(0.0, 1.0 - latency / 1000.0)  # Assuming 1000ms is the threshold for a score of 0
        return Score(
            name=self.name,
            value=value,
            details={"latency_ms": latency},
        )

      
        
    
