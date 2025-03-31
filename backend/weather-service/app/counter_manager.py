from datetime import datetime, timedelta, timezone

class RequestCounter:
    def __init__(self, daily_limit=1000):
        self.daily_limit = daily_limit
        self.counter = 0
        self.reset_time = datetime.now(timezone.utc).date()  # Use today's date
        self.reset_time = datetime.combine(self.reset_time, datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)  # Next midnight

    def increment(self):
        """Reset the counter if a new day has started, then increment the request counter."""
        current_time = datetime.now(timezone.utc)
        if current_time.date() > self.reset_time.date():  # Check if the day has changed
            self.counter = 0
            self.reset_time = datetime.combine(current_time.date(), datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
        
        if self.counter < self.daily_limit:
            self.counter += 1
        else:
            raise Exception("Daily request limit reached")

    def get_count(self):
        """Return the current request counter value."""
        return self.counter
