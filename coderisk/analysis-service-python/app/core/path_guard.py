from pathlib import Path


def ensure_path_under_root(candidate: str, root: str) -> bool:
    root_path = Path(root).expanduser().resolve(strict=False)
    candidate_path = Path(candidate).expanduser().resolve(strict=False)
    try:
        candidate_path.relative_to(root_path)
    except ValueError:
        return False
    return True
