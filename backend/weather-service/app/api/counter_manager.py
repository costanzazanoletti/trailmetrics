from datetime import datetime, timedelta, timezone

class RequestCounter:
    def __init__(self, daily_limit=1000):
        self.daily_limit = daily_limit
        self.counter = 0
        # Use today's date to calculate the next midnight
        self.reset_time = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)

    def increment(self):
        """Reset the counter if a new day has started, then increment the request counter."""
        current_time = datetime.now(timezone.utc)
        
        # Check if the day has changed and reset the counter
        if current_time >= self.reset_time:  
            self.counter = 0
            # Set the reset time to the next midnight
            self.reset_time = datetime.combine(current_time.date(), datetime.min.time(), tzinfo=timezone.utc) + timedelta(days=1)
        
        # Increment the counter if below the daily limit
        if self.counter < self.daily_limit:
            self.counter += 1
        else:
            raise Exception("Daily request limit reached")

    def get_count(self):
        """Return the current request counter value."""
        return self.counter
