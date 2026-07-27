from evalforge.prompts.store import get_version
import difflib

def diff_versions(a: str, b: str, label_a: str = "old", label_b: str = "new") -> str:
    """
    Return a unified diff string between two prompt contents.
    Use difflib.unified_diff.
    """
    return "\n".join(difflib.unified_diff(a.splitlines(), b.splitlines(), label_a, label_b))


def diff_by_hash(hash_a: str, hash_b: str, out: str = "results") -> str:
    """
    Look up both versions from the store, then call diff_versions.
    Use the hash as the label.
    """
    v_a = get_version(hash_a, out)
    v_b = get_version(hash_b, out)
    if v_a is None or v_b is None:
        raise ValueError("One or both hashes not found.")
    return diff_versions(v_a["content"], v_b["content"], hash_a, hash_b)
