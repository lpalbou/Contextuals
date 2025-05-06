"""Exceptions for the Contextuals library."""

class ContextualsError(Exception):
    """Base exception for Contextuals library."""
    pass


class APIError(ContextualsError):
    """Error when interacting with external APIs."""
    pass


class ConfigurationError(ContextualsError):
    """Error in configuration."""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Missing required API key."""
    def __init__(self, service):
        self.service = service
        message = (f"Missing API key for {service}. "
                  f"Set the CONTEXTUALS_{service.upper()}_API_KEY environment variable "
                  f"or pass it directly when initializing Contextuals.")
        super().__init__(message)


class NetworkError(ContextualsError):
    """Network-related error."""
    pass


class FallbackError(ContextualsError):
    """Error when all fallback mechanisms fail."""
    pass
