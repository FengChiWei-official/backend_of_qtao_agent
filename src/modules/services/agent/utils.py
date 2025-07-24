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


class Looper:
    """
    A utility class to handle looping operations with a maximum count.
    """
    def __init__(self, max_count: int):
        self.max_count = max_count
        self.current_count = 0

    def reset(self):
        self.current_count = 0

    def increment(self):
        if self.current_count < self.max_count:
            self.current_count += 1
        else:
            raise ValueError("Maximum loop count exceeded.")
    
    def break_loop(self):
        """
        Break the loop by setting the current count to max_count.
        """
        self.current_count = self.max_count * 2

    def is_maxed_out(self) -> bool:
        return self.current_count > self.max_count