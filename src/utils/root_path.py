from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=1)
def get_root_path() -> Path:
    for i in range(10):
        t = Path(__file__).resolve().parents[i]
        if t.name == 'backend':
            return t
    raise FileNotFoundError("Project root not found in the expected directory structure.")
