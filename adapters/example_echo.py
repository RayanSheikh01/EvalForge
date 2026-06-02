from evalforge.agent import Agent, AgentRun, ToolCall


echo_agent = Agent("EchoAgent",
                   lambda input: AgentRun(output=input, tool_calls=[ToolCall("web_search", {"query": input})], token_usage=len(input), latency_ms=0.0, error=""))





