"""Configuration management for Contextuals."""

import os
from typing import Dict, Any, Optional
import dotenv

# Load environment variables from .env file if present
dotenv.load_dotenv()

class Config:
    """Configuration management for Contextuals.
    
    Handles API keys, cache settings, and other configuration options.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        # Cache settings
        "cache_enabled": True,
        "cache_duration": 300,  # 5 minutes in seconds
        
        # API endpoints
        "time_api_url": "http://worldtimeapi.org/api/ip",
        "weather_api_url": "https://api.openweathermap.org/data/2.5/weather",
        "weather_forecast_api_url": "https://api.openweathermap.org/data/2.5/forecast",
        "weather_onecall_api_url": "https://api.openweathermap.org/data/3.0/onecall",
        "weather_air_quality_api_url": "https://api.openweathermap.org/data/2.5/air_pollution",
        "location_api_url": "https://nominatim.openstreetmap.org/search",
        "news_api_url": "https://newsapi.org/v2/top-headlines",
        "news_search_api_url": "https://newsapi.org/v2/everything",
        
        # Default values
        "default_country": "us",  # Used when no location is available
        
        # Fallback settings
        "use_fallback": True,
    }
    
    # Environment variable names for API keys
    ENV_VAR_MAPPING = {
        "weather_api_key": "CONTEXTUALS_WEATHER_API_KEY",
        "location_api_key": "CONTEXTUALS_LOCATION_API_KEY",
        "news_api_key": "CONTEXTUALS_NEWS_API_KEY",
    }
    
    def __init__(self, **kwargs):
        """Initialize configuration with optional overrides.
        
        Args:
            **kwargs: Configuration overrides.
        """
        self._config = self.DEFAULT_CONFIG.copy()
        
        # Load API keys from environment variables
        for config_key, env_var in self.ENV_VAR_MAPPING.items():
            env_value = os.environ.get(env_var)
            if env_value:
                self._config[config_key] = env_value
        
        # Apply any overrides passed as kwargs
        self._config.update(kwargs)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: The configuration key to retrieve.
            default: Default value if key is not found.
            
        Returns:
            The configuration value or default.
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: The configuration key to set.
            value: The value to set.
        """
        self._config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update multiple configuration values.
        
        Args:
            config_dict: Dictionary of configuration values to update.
        """
        self._config.update(config_dict)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service.
        
        Args:
            service: Service name (e.g., 'weather', 'location').
            
        Returns:
            API key if available, None otherwise.
        """
        key = f"{service}_api_key"
        return self._config.get(key)
    
    def set_api_key(self, service: str, api_key: str) -> None:
        """Set API key for a specific service.
        
        Args:
            service: Service name (e.g., 'weather', 'location').
            api_key: The API key value.
        """
        key = f"{service}_api_key"
        self._config[key] = api_key
