    

from evalforge.scoring.base import Score, Scorer


PRICING = {
    "default": (0.0001, 0.0002),  # (input_cost_per_token, output_cost_per_token)
}

class TokenCostScorer(Scorer):
    name = "TokenCostScorer"

    def score(self, task, agent_run) -> Score:
        if not agent_run.token_usage:
            return Score(
                name=self.name,
                value=0.0,
                details={"error": "No token usage data available"},
            )

        input_cost_per_token, output_cost_per_token = PRICING.get("default", (0.0001, 0.0002))
        total_cost = (
            agent_run.token_usage.input_tokens * input_cost_per_token +
            agent_run.token_usage.output_tokens * output_cost_per_token
        )
        # Convert cost to a score between 0 and 1 (lower cost is better)
        value = max(0.0, 1.0 - total_cost / 10.0)  # Assuming $10 is the threshold for a score of 0
        return Score(
            name=self.name,
            value=value,
            details={
                "input_tokens": agent_run.token_usage.input_tokens,
                "output_tokens": agent_run.token_usage.output_tokens,
                "total_cost": total_cost,
            },
        )
