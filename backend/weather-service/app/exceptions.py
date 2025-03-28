
class WeatherAPIException(Exception):
    def __init__(self, message, status_code=None, retry_in_hour=False):
        super().__init__(message)
        self.status_code = status_code
        self.retry_in_hour = retry_in_hour
