from evalforge.scoring.base import Score, Scorer


def _arg_match(expected: dict, actual: dict) -> bool:
    """Match expected arg matchers against actual call args.
    A value of "*" means "any value, key must be present"; otherwise the
    actual value must equal the expected value exactly."""
    for k, v in expected.items():
        if v == "*":
            if k not in actual:
                return False
        elif actual.get(k) != v:
            return False
    return True


class ToolAccuracyScorer(Scorer):
    name = "ToolAccuracyScorer"

    def score(self, task, agent_run) -> Score:
        expected = task.expected_tools
        if not expected:
            return Score(name=self.name, value=1.0, details={"matched": 0, "total": 0})

        actual = list(agent_run.tool_calls)
        matched = 0
        for exp in expected:
            for i, call in enumerate(actual):
                if call.name == exp.name and _arg_match(exp.args, call.args):
                    matched += 1
                    del actual[i]
                    break

        value = matched / len(expected)
        return Score(
            name=self.name,
            value=value,
            details={"matched": matched, "total": len(expected)},
        )
