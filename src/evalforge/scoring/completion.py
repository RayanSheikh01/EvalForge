    

from evalforge.scoring.base import Score, Scorer

class CompletionScorer(Scorer):
    name = "CompletionScorer"
    
    def score(self, task, agent_run):
        # For simplicity, we will just check if the output is non-empty
        value = 1.0 if agent_run.output else 0.0
        return Score(name=self.name, value=value, details={"output_length": len(agent_run.output)})
    




