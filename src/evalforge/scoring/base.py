from dataclasses import dataclass
from typing import Protocol

from evalforge.agent import AgentRun

@dataclass
class Score:
    name: str
    value: float
    details: dict

class Scorer(Protocol):
    name: str
    
    def score(self, task, agent_run: AgentRun) -> Score:
        ...

