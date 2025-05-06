"""Main entry point for Contextuals library."""

import datetime
from typing import Dict, Any, Optional

from contextuals.core.config import Config
from contextuals.core.cache import Cache
from contextuals.core.context_manager import ContextManager
from contextuals.time.time_provider import TimeProvider


class Contextuals:
    """Main class for accessing contextual information.
    
    Provides a unified interface to access different types of contextual information
    such as time, weather, location, etc.
    """
    
    def __init__(self, **kwargs):
        """Initialize Contextuals with optional configuration.
        
        Args:
            **kwargs: Configuration options to override defaults.
            
        Example:
            ```python
            # Initialize with default configuration
            context = Contextuals()
            
            # Initialize with custom configuration
            context = Contextuals(
                cache_duration=600,  # 10 minutes
                weather_api_key="your_api_key"
            )
            ```
        """
        self.config = Config(**kwargs)
        self.cache = Cache(default_ttl=self.config.get("cache_duration"))
        self.context_manager = ContextManager(self.config, self.cache)
        
        # Initialize providers
        self._time = TimeProvider(self.config, self.cache, self.context_manager)
        # Weather, location, news, and system providers will be initialized lazily
        self._weather = None
        self._location = None
        self._news = None
        self._system = None
    
    @property
    def time(self):
        """Access time-related contextual information.
        
        Returns:
            TimeProvider instance.
        """
        return self._time
    
    @property
    def weather(self):
        """Access weather-related contextual information.
        
        Returns:
            WeatherProvider instance.
            
        Raises:
            ImportError: If the weather module is not available.
        """
        if self._weather is None:
            from contextuals.weather.weather_provider import WeatherProvider
            self._weather = WeatherProvider(self.config, self.cache)
        return self._weather
    
    @property
    def location(self):
        """Access location-related contextual information.
        
        Returns:
            LocationProvider instance.
            
        Raises:
            ImportError: If the location module is not available.
        """
        if self._location is None:
            from contextuals.location.location_provider import LocationProvider
            self._location = LocationProvider(self.config, self.cache, self.context_manager)
        return self._location
    
    @property
    def news(self):
        """Access news-related contextual information.
        
        Returns:
            NewsProvider instance.
            
        Raises:
            ImportError: If the news module is not available.
        """
        if self._news is None:
            from contextuals.news.news_provider import NewsProvider
            self._news = NewsProvider(self.config, self.cache, self.context_manager)
        return self._news
    
    @property
    def system(self):
        """Access system-related contextual information.
        
        Returns:
            SystemProvider instance.
            
        Raises:
            ImportError: If the system module is not available.
        """
        if self._system is None:
            from contextuals.system.system_provider import SystemProvider
            self._system = SystemProvider(self.config, self.cache, self.context_manager)
        return self._system
    
    def update_config(self, **kwargs):
        """Update configuration.
        
        Args:
            **kwargs: Configuration options to update.
        """
        self.config.update(kwargs)
    
    def set_api_key(self, service: str, api_key: str):
        """Set API key for a specific service.
        
        Args:
            service: Service name (e.g., 'weather', 'location', 'news').
            api_key: The API key.
        """
        self.config.set_api_key(service, api_key)
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
    
    def get_current_datetime(self):
        """Get the current date and time.
        
        Returns:
            Current datetime.
        """
        return self.context_manager.get_current_datetime()
    
    def set_current_location(self, location_name: str):
        """Set the current location by name.
        
        Args:
            location_name: Name of the location.
            
        Raises:
            ImportError: If the location module is not available.
            Exception: If the location cannot be found.
        """
        # Ensure location provider is initialized
        if self._location is None:
            from contextuals.location.location_provider import LocationProvider
            self._location = LocationProvider(self.config, self.cache, self.context_manager)
        
        # Get location data and set as current location
        location_data = self._location.get(location_name)
        self.context_manager.set_current_location(location_data)
        
        return location_data
    
    def get_all_context(self) -> Dict[str, Any]:
        """Get all available contextual information.
        
        Returns:
            Dictionary with all contextual information.
        """
        response_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Collect all contextual information
        result = {
            "timestamp": response_time,
            "request_time": response_time,
            "type": "all_context",
            "is_cached": False,
        }
        
        # Add time information - time is always available locally even offline
        try:
            result["time"] = self.time.now(format_as_json=True)
        except Exception as e:
            # This is a fallback in case of unexpected errors, but time should always work
            fallback_time = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "current_time",
                "is_cached": False,
                "data": {
                    "iso": response_time,
                    "timestamp": int(datetime.datetime.now().timestamp()),
                    "timezone": "UTC",
                    "note": "Fallback time due to error"
                }
            }
            result["time"] = fallback_time
        
        # Add location information - may require internet
        try:
            # Try to get current location first from context manager (cached)
            current_location = self.context_manager.get_current_location()
            if current_location:
                result["location"] = current_location
            else:
                # Otherwise, try to detect location (may need internet)
                try:
                    result["location"] = self.location.get_current_location()
                except Exception as loc_e:
                    # If location detection fails, provide a graceful fallback
                    result["location"] = {
                        "timestamp": response_time,
                        "request_time": response_time,
                        "type": "location_unavailable",
                        "is_cached": False,
                        "data": {
                            "status": "unavailable",
                            "reason": str(loc_e),
                            "note": "Location services unavailable - possibly offline"
                        }
                    }
        except Exception as e:
            result["location"] = {
                "timestamp": response_time,
                "type": "location_error",
                "error": str(e),
                "data": {"status": "unavailable"}
            }
        
        # Add weather information if location is available
        weather_error = None
        try:
            if "location" in result and "error" not in result["location"] and result["location"].get("type") != "location_unavailable":
                loc_name = None
                if "name" in result["location"]:
                    loc_name = result["location"]["name"]
                elif "data" in result["location"] and "name" in result["location"]["data"]:
                    loc_name = result["location"]["data"]["name"]
                
                if loc_name:
                    # Try to get weather data with graceful fallbacks if APIs are unavailable
                    try:
                        result["weather"] = self.weather.current(loc_name)
                    except Exception as e:
                        weather_error = str(e)
                        result["weather"] = {
                            "timestamp": response_time,
                            "type": "weather_unavailable",
                            "is_cached": False,
                            "data": {"status": "unavailable", "reason": str(e)}
                        }
                    
                    # Only try additional weather data if basic weather worked
                    if "error" not in result["weather"] and result["weather"].get("type") != "weather_unavailable":
                        try:
                            result["weather_detailed"] = self.weather.get_detailed_weather(loc_name)
                        except Exception:
                            result["weather_detailed"] = {"type": "weather_detail_unavailable", "data": {"status": "unavailable"}}
                        
                        try:
                            result["air_quality"] = self.weather.get_air_quality(loc_name)
                        except Exception:
                            result["air_quality"] = {"type": "air_quality_unavailable", "data": {"status": "unavailable"}}
                        
                        try:
                            result["astronomy"] = self.weather.get_astronomy(loc_name)
                        except Exception:
                            result["astronomy"] = {"type": "astronomy_unavailable", "data": {"status": "unavailable"}}
                    else:
                        # If basic weather failed, don't even try the other APIs
                        result["weather_detailed"] = {"type": "weather_detail_unavailable", "data": {"status": "unavailable"}}
                        result["air_quality"] = {"type": "air_quality_unavailable", "data": {"status": "unavailable"}}
                        result["astronomy"] = {"type": "astronomy_unavailable", "data": {"status": "unavailable"}}
            else:
                # No location available, so weather is also unavailable
                weather_error = "Location information unavailable"
                result["weather"] = {
                    "timestamp": response_time,
                    "type": "weather_unavailable",
                    "is_cached": False,
                    "data": {"status": "unavailable", "reason": "Location information required for weather"}
                }
        except Exception as e:
            weather_error = str(e)
            result["weather"] = {
                "timestamp": response_time,
                "type": "weather_error",
                "error": str(e),
                "data": {"status": "error"}
            }
        
        # Add news information - this requires internet access
        try:
            # Always use world news by default for the "all" command
            try:
                result["news"] = self.news.get_world_news()
            except Exception as e:
                result["news"] = {
                    "timestamp": response_time,
                    "type": "news_unavailable",
                    "is_cached": False,
                    "data": {"status": "unavailable", "reason": str(e)}
                }
        except Exception as e:
            result["news"] = {
                "timestamp": response_time,
                "type": "news_error",
                "error": str(e),
                "data": {"status": "unavailable"}
            }
        
        # System information is not included by default as it may not be available or relevant
        # for all platforms and use cases
        
        return result
