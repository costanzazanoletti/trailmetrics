# counter_manager.py
import time
from datetime import datetime, timedelta, timezone

class RequestCounter:
    def __init__(self, daily_limit=1000):
        self.daily_limit = daily_limit
        self.counter = 0
        self.reset_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    def increment(self):
        """Try to reset the counter, then increment the request counter."""
        if datetime.now(datetime.timezone.utc) >= self.reset_time:
            self.counter = 0
            self.reset_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        if self.counter < self.daily_limit:
            self.counter += 1
        else:
            raise Exception("Daily request limit reached")


    def get_count(self):
        """Return the current request counter value."""
        return self.counter
