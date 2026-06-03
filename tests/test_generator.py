import pytest

def test_generator(monkeypatch):
    from generator.generator import generate
    from generator.categories import CATEGORIES
    category = CATEGORIES["ambiguous"]
    model = "ollama:evalforge-test"
    # Mock the _chat function to return a fixed response
    def mock_chat(model: str, messages: list[dict[str, str]], **kwargs
    ) -> str:
        return """
        [
            {
                "id": "task-001",
                "description": "A test task",
                "input": "Test input",
                "expected_tools": [{"name": "tool1", "args": {"arg1": "value1"}}],
                "expected_output": {"contains": ["expected output"]},
                "metadata": {"failure_indicators": ["indicator1"], "category": "ambiguous"}
            },
            {
                "id": "task-002",
                "description": "Another test task",
                "input": "Another test input",
                "expected_tools": [],
                "expected_output": {"contains": ["another expected output"]},
                "metadata": {"failure_indicators": ["indicator2"], "category": "ambiguous"}
            },
            {
                "id": "task-003",
                "description": "Yet another test task",
                "input": "Yet another test input",
                "expected_tools": [{"name": "tool2"}],
                "expected_output": {"contains": ["yet another expected output"]},
                "metadata": {"failure_indicators": ["indicator3"], "category": "ambiguous"}
            },
            {
                "id": "task-004",
                "description": "",
                "input": "",
                "expected_tools": [],
                "expected_output": {},
                "metadata": {}
            },
            {
                "id": "task-005",
                "description": "",
                "input": "",
                "expected_tools": [],
                "expected_output": {},
                "metadata": {}
            }
        ]
        """
    monkeypatch.setattr("generator.generator._chat", mock_chat)
    tasks = generate(category, 5, model)
    assert len(tasks) == 5, "Should generate the specified number of tasks"
    for task in tasks:
        assert hasattr(task, 'id'), "Task should have an id"
        assert hasattr(task, 'description'), "Task should have a description"
        assert hasattr(task, 'input'), "Task should have input"
        assert hasattr(task, 'expected_tools'), "Task should have expected tools"
        assert hasattr(task, 'expected_output'), "Task should have expected output"
        assert hasattr(task, 'metadata'), "Task should have metadata"
        assert isinstance(task.expected_tools, list), "Expected tools should be a list"
        assert isinstance(task.expected_output, dict), "Expected output should be a dict"
        assert isinstance(task.metadata, dict), "Metadata should be a dict"
        
    
    