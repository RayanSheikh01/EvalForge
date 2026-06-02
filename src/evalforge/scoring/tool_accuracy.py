from evalforge.scoring.base import Score, Scorer


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
                if call.name == exp.name and call.args == exp.args:
                    matched += 1
                    del actual[i]
                    break

        value = matched / len(expected)
        return Score(
            name=self.name,
            value=value,
            details={"matched": matched, "total": len(expected)},
        )
