"""Exceptions for the Contextual-CC library."""

class ContextualCCError(Exception):
    """Base exception for Contextual-CC library."""
    pass


class APIError(ContextualCCError):
    """Error when interacting with external APIs."""
    pass


class ConfigurationError(ContextualCCError):
    """Error in configuration."""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Missing required API key."""
    def __init__(self, service):
        self.service = service
        message = (f"Missing API key for {service}. "
                  f"Set the CONTEXTUAL_CC_{service.upper()}_API_KEY environment variable "
                  f"or pass it directly when initializing ContextualCC.")
        super().__init__(message)


class NetworkError(ContextualCCError):
    """Network-related error."""
    pass


class FallbackError(ContextualCCError):
    """Error when all fallback mechanisms fail."""
    pass
