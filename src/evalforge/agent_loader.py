import importlib
import os
import sys


def load_agent(spec):
    """spec is "module.path:ClassName" — import and instantiate."""
    module_name, _, cls_name = spec.partition(":")
    if not cls_name:
        raise ValueError(f"Agent spec must be 'module:ClassName', got: {spec!r}")
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    mod = importlib.import_module(module_name)
    return getattr(mod, cls_name)()
