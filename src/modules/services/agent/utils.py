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
        self.current_count += 1

    
    def break_loop(self):
        """
        Break the loop by setting the current count to max_count.
        """
        self.current_count = self.max_count * 2

    def is_maxed_out(self) -> bool:
        return self.current_count > self.max_count