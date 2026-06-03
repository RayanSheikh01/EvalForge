import pytest


def test_load_tasks_recurses_into_subdirs(tmp_path):
    from evalforge.task import load_tasks

    top = tmp_path / "top.yaml"
    top.write_text("id: top\ninput: hi\n")
    sub = tmp_path / "generated"
    sub.mkdir()
    (sub / "nested.yaml").write_text("id: nested\ninput: yo\n")

    ids = {t.id for t in load_tasks(str(tmp_path))}
    assert ids == {"top", "nested"}


def test_task_loading():
    from evalforge.task import Task
    tasks = Task.load_tasks('tasks/example_task.yaml')
    assert len(tasks) == 1
    task = tasks[0]
    assert task.id == 'echo_web_search'
    assert task.input == 'search for echo chambers'
    assert task.description == 'Echo agent should restate the input and call web_search once.'
    assert len(task.expected_tools) == 1
    assert task.expected_tools[0].name == 'web_search'
    assert task.expected_tools[0].args['query'] == '*'
    assert 'echo' in task.expected_output['contains']
    assert 'smoke' in task.metadata['tags']
    
    # test with file in a subdirectory
    tasks = Task.load_tasks('tasks/subdir/example_task.yaml')
    assert len(tasks) == 1
    task = tasks[0]
    assert task.id == 'echo_web_search'
    assert task.input == 'search for echo chambers'
    assert task.description == 'Echo agent should restate the input and call web_search once.'
    assert len(task.expected_tools) == 1
    assert task.expected_tools[0].name == 'web_search'
    assert task.expected_tools[0].args['query'] == '*'