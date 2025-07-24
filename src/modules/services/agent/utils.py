from os import path
from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=1)
def get_root_path() -> Path | None:
    for i in range(10):
        t = Path(__file__).resolve().parents[i]
        if t.name == 'backend':
            return t
    raise FileNotFoundError("Project root not found in the expected directory structure.")

PATH_TO_ROOT = get_root_path()

if __name__ == "__main__":
    print(f"Project root path: {PATH_TO_ROOT}")