"""Pytest configuration file for the project."""

import os
import pytest
from unittest.mock import MagicMock

from contextuals.core.config import Config
from contextuals.core.cache import Cache
from contextuals import Contextuals


def get_api_key(service_name):
    """Get an API key from environment variables.
    
    Args:
        service_name: The service name (e.g., 'weather', 'news', 'location')
        
    Returns:
        The API key if available, None otherwise.
    """
    env_var_name = f"CONTEXTUALS_{service_name.upper()}_API_KEY"
    return os.environ.get(env_var_name)


def requires_api_key(service_name):
    """Decorator to skip a test if an API key is not available.
    
    Args:
        service_name: The service name (e.g., 'weather', 'news', 'location')
    """
    key = get_api_key(service_name)
    return pytest.mark.skipif(
        key is None,
        reason=f"No API key available for {service_name}. Set CONTEXTUALS_{service_name.upper()}_API_KEY environment variable."
    )


@pytest.fixture
def contextuals():
    """Create a Contextuals instance for testing."""
    return Contextuals()


@pytest.fixture
def config():
    """Create a Config instance for testing."""
    return Config()


@pytest.fixture
def cache():
    """Create a Cache instance for testing."""
    return Cache()


@pytest.fixture(scope="session")
def real_time_provider():
    """Create a real TimeProvider instance for testing."""
    context = Contextuals()
    return context.time


@pytest.fixture(scope="session")
def real_weather_provider():
    """Create a real WeatherProvider instance for testing.
    Only used when CONTEXTUALS_WEATHER_API_KEY is available."""
    context = Contextuals()
    if get_api_key("weather") is not None:
        return context.weather
    return None


@pytest.fixture(scope="session")
def real_location_provider():
    """Create a real LocationProvider instance for testing."""
    context = Contextuals()
    return context.location


@pytest.fixture(scope="session")
def real_news_provider():
    """Create a real NewsProvider instance for testing.
    Only used when CONTEXTUALS_NEWS_API_KEY is available."""
    context = Contextuals()
    if get_api_key("news") is not None:
        return context.news
    return None