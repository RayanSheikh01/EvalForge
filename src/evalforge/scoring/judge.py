    

import ollama

from evalforge.agent import AgentRun
from evalforge.scoring.base import Score


def _chat(model, messages) -> str:
    
    resp = ollama.chat(model=model, messages=messages, format="json", options={"temperature": 0})
    return resp["message"]["content"]

class JudgeScorer:
    name = "JudgeScorer"

    def score(self, task, agent_run) -> Score:
        messages = [
            {"role": "system", "content": f"You are a helpful and precise assistant for checking the quality of the answer."},
            {"role": "user", "content": f"""Question: {task.input}
Answer: {agent_run.output}
Please score the answer on a scale of 0 to 1, where 1 is a perfect answer and 0 is a completely wrong answer. Only provide the score as a number without any explanation."""},
        ]
        score_str = _chat("evalforge/judge", messages)
        try:
            score_value = float(score_str.strip())
        except ValueError:
            score_value = 0.0  # Default to 0 if parsing fails
        return Score(
            name=self.name,
            value=score_value,
            details={"raw_score": score_str},
        )
    
