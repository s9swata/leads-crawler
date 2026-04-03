"""Custom exceptions for lead-gen CLI."""


class LeadGenError(Exception):
    """Base exception for all lead-gen errors."""

    @property
    def user_message(self) -> str:
        """User-friendly message for CLI output."""
        return "An error occurred. Please try again."

    @property
    def technical_details(self) -> str:
        """Technical details for debug mode."""
        return str(self)


class APIKeyError(LeadGenError):
    """Raised when an API key is not configured."""

    def __init__(self, key_name: str):
        self.key_name = key_name
        super().__init__(f"API key '{key_name}' not configured")

    @property
    def user_message(self) -> str:
        return f"API key not configured. Set {self.key_name} in your .env file"

    @property
    def technical_details(self) -> str:
        return f"Missing API key: {self.key_name}"


class NetworkError(LeadGenError):
    """Raised when a network error occurs."""

    def __init__(self, message: str = "Network error"):
        self.message = message
        super().__init__(message)

    @property
    def user_message(self) -> str:
        return "Network error. Check your connection and retry."

    @property
    def technical_details(self) -> str:
        return f"Network error: {self.message}"


class RateLimitError(LeadGenError):
    """Raised when rate limited by an API."""

    def __init__(self, seconds: int):
        self.seconds = seconds
        super().__init__(f"Rate limited for {seconds} seconds")

    @property
    def user_message(self) -> str:
        return f"Rate limited. Wait {self.seconds} seconds before retrying."

    @property
    def technical_details(self) -> str:
        return f"Rate limit hit. Retry after {self.seconds} seconds."


class ScrapingError(LeadGenError):
    """Raised when scraping fails."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"Failed to scrape {url}: {reason}")

    @property
    def user_message(self) -> str:
        return f"Failed to scrape {self.url}: {self.reason}"

    @property
    def technical_details(self) -> str:
        return f"URL: {self.url}, Reason: {self.reason}"


class ConfigurationError(LeadGenError):
    """Raised when there's a configuration error."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(f"Configuration error: {detail}")

    @property
    def user_message(self) -> str:
        return f"Configuration error: {self.detail}"

    @property
    def technical_details(self) -> str:
        return f"Configuration error: {self.detail}"
