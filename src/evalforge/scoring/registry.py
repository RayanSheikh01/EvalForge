


from evalforge.scoring.completion import CompletionScorer
from evalforge.scoring.latency import LatencyScorer
from evalforge.scoring.token_cost import TokenCostScorer
from evalforge.scoring.tool_accuracy import ToolAccuracyScorer


DEFAULT_SCORERS = {
    "latency": LatencyScorer(),
    "token_cost": TokenCostScorer(),
    "completion": CompletionScorer(),
    "tool_accuracy": ToolAccuracyScorer()
}