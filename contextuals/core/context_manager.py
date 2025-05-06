"""Context manager for maintaining and providing contextual information."""

import datetime
import time
from typing import Dict, Any, Optional

from contextuals.core.config import Config
from contextuals.core.cache import Cache


class ContextManager:
    """Central manager for contextual information.
    
    Provides access to current date, location, and other context information
    that needs to be consistent across the library.
    """
    
    def __init__(self, config: Config, cache: Cache):
        """Initialize context manager.
        
        Args:
            config: Configuration instance.
            cache: Cache instance.
        """
        self.config = config
        self.cache = cache
        self._current_location = None
        self._last_time_sync = 0
        self._time_offset = 0  # Offset between local and server time
        self._sync_interval = config.get("time_sync_interval", 300)  # 5 minutes
    
    def get_current_datetime(self) -> datetime.datetime:
        """Get the current date and time.
        
        Uses time synced with an external time API when available.
        
        Returns:
            Current datetime with the proper timezone.
        """
        # Check if we need to sync with the time API
        current_time = time.time()
        if (current_time - self._last_time_sync) > self._sync_interval:
            self._sync_time()
        
        # Get the current time with offset applied
        current_time = time.time() + self._time_offset
        return datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc)
    
    def get_current_datetime_iso(self) -> str:
        """Get the current date and time in ISO format.
        
        Returns:
            Current datetime in ISO format.
        """
        return self.get_current_datetime().isoformat()
    
    def _sync_time(self) -> None:
        """Sync time with an external time API.
        
        Updates the time offset and last sync time.
        """
        # Try to get cached time offset first
        cached_offset = self.cache.get("time_offset")
        if cached_offset is not None:
            self._time_offset = cached_offset
            self._last_time_sync = time.time()
            return
        
        # Otherwise, try to sync with the time API
        try:
            import requests
            api_url = self.config.get("time_api_url", "http://worldtimeapi.org/api/ip")
            
            # Record local time before the request
            local_time_before = time.time()
            
            # Make the request
            response = requests.get(api_url, timeout=5)
            
            # Record local time after the request
            local_time_after = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                # Calculate the offset
                server_time = data.get("unixtime")
                # Use the midpoint of the request for better accuracy
                local_time = (local_time_before + local_time_after) / 2
                
                # Calculate and store the offset
                self._time_offset = server_time - local_time
                self._last_sync_time = local_time
                
                # Cache the offset
                self.cache.set("time_offset", self._time_offset, self._sync_interval)
        except Exception:
            # If sync fails, use local time (offset=0)
            pass
        
        # Update last sync time even if sync failed
        self._last_time_sync = time.time()
    
    def set_current_location(self, location: Dict[str, Any]) -> None:
        """Set the current location context.
        
        Args:
            location: Location information.
        """
        self._current_location = location
        
        # Cache the location
        self.cache.set("current_location", location)
    
    def get_current_location(self) -> Optional[Dict[str, Any]]:
        """Get the current location context.
        
        Returns:
            Current location information or None if not set.
        """
        if self._current_location is None:
            # Try to get from cache
            cached_location = self.cache.get("current_location")
            if cached_location is not None:
                self._current_location = cached_location
        
        return self._current_location
    
    def get_current_country(self) -> Optional[str]:
        """Get the current country from location context.
        
        Returns:
            Current country code or None if not available.
        """
        location = self.get_current_location()
        if location and "country" in location:
            return location["country"]
        return None
    
    def create_response_context(self) -> Dict[str, Any]:
        """Create a context object to include in responses.
        
        Returns:
            Dictionary with context information.
        """
        context = {
            "timestamp": self.get_current_datetime_iso(),
            "timezone": "UTC",
        }
        
        # Add location context if available
        location = self.get_current_location()
        if location:
            context["location"] = {
                "name": location.get("name"),
                "country": location.get("country"),
                "coordinates": location.get("coordinates", {})
            }
        
        return context
    
    def format_response(self, data: Any, response_type: str) -> Dict[str, Any]:
        """Format data into a standardized response with context.
        
        Args:
            data: The data to format.
            response_type: Type of response (e.g., 'weather', 'news').
        
        Returns:
            Formatted response with context.
        """
        return {
            "context": self.create_response_context(),
            "type": response_type,
            "data": data
        }