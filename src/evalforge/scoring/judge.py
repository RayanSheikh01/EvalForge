    

import json
import os

import ollama

from evalforge.scoring.base import Score


def _chat(model, messages) -> str:
    
    resp = ollama.chat(model=model, messages=messages, format="json", options={"temperature": 0})
    return resp["message"]["content"]

class JudgeScorer:
    name = "JudgeScorer"

    def score(self, task, agent_run) -> Score:
        rubric = task.expected_output.get("rubric")
        if not rubric:
            return Score(name=self.name, value=1.0, details={"note": "no rubric"})
        messages = [
            {"role": "system", "content": "You are a strict grader. Given a rubric and "
             "an agent's answer, return JSON {\"score\": <float 0..1>, \"reason\": <str>} "
             "and nothing else."},
            {"role": "user", "content": f"""Question: {task.input}
Rubric: {rubric}
Answer: {agent_run.output}"""},
        ]
        model = os.environ.get("EVALFORGE_JUDGE_MODEL", "llama3.2")
        try:
            raw = _chat(model, messages)
            data = json.loads(raw)
            score_value = max(0.0, min(1.0, float(data["score"])))  # clamp to [0, 1]
            return Score(
                name=self.name,
                value=score_value,
                details={"reason": data.get("reason"), "model": model},
            )
        except Exception as e:
            # Judge must never re-raise: a dead daemon / missing model would
            # otherwise crash the whole run (runner.py:35). Degrade to 0.0.
            return Score(name=self.name, value=0.0, details={"error": str(e), "model": model})
    
