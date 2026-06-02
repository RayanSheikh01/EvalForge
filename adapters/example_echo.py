from evalforge.agent import AgentRun, ToolCall, TokenUsage


class EchoAgent:
    name = "EchoAgent"

    def run(self, input: str) -> AgentRun:
        return AgentRun(
            output=input,
            tool_calls=[ToolCall("web_search", {"query": input})],
            token_usage=TokenUsage(input_tokens=len(input), output_tokens=len(input)),
            latency_ms=0.0,
            error="",
        )


echo_agent = EchoAgent()
