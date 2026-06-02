from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

@dataclass
class ToolCall:
    name: str
    args: Dict[]
    results: Any = None
    
@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    
@dataclass
class AgentRun:
    output: str
    tool_calls: List[ToolCall]
    token_usage: Optional[TokenUsage]
    latency_ms: float = 0.0
    eror: str = ""
    
class Agent(Protocol):
    name: str
    
    def run(self, input: str) -> AgentRun:
        ...
    
