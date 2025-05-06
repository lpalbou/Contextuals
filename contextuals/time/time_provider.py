"""Time provider for Contextuals."""

import time
import datetime
import json
from typing import Optional, Dict, Any, Union
import threading
import requests

from contextuals.core.cache import Cache, cached
from contextuals.core.config import Config
from contextuals.core.exceptions import APIError, NetworkError, FallbackError


class TimeProvider:
    """Provides time-related contextual information.
    
    Features:
    - Synchronizes with an external time API to get accurate time
    - Falls back to local time when API is not available
    - Maintains cached offset for efficient time calculations
    - Periodically re-syncs with the API
    - Returns structured JSON responses with timestamps
    """
    
    def __init__(self, config: Config, cache: Cache, context_manager=None):
        """Initialize the time provider.
        
        Args:
            config: Configuration instance.
            cache: Cache instance.
            context_manager: Optional context manager instance.
        """
        self.config = config
        self.cache = cache
        self.context_manager = context_manager
        self._offset = 0  # Offset in seconds between local time and server time
        self._last_sync = 0  # Timestamp of last successful sync
        self._lock = threading.Lock()  # Lock for thread safety
        
        # Try to sync with the time API on initialization
        self._sync_time()
        
        # Start a background thread for periodic sync if enabled
        if self.config.get("time_auto_sync", True):
            self._start_sync_thread()
    
    def _start_sync_thread(self):
        """Start a background thread for periodic time synchronization."""
        sync_interval = self.config.get("time_sync_interval", 300)  # 5 minutes by default
        
        def sync_worker():
            while True:
                time.sleep(sync_interval)
                try:
                    self._sync_time()
                except Exception:
                    # Silently ignore errors in the background thread
                    pass
        
        thread = threading.Thread(target=sync_worker, daemon=True)
        thread.start()
    
    def _sync_time(self) -> bool:
        """Synchronize with the time API to calculate the offset.
        
        Returns:
            True if sync was successful, False otherwise.
        """
        with self._lock:
            # Try to get from cache first
            cached_offset = self.cache.get("time_offset")
            if cached_offset is not None:
                self._offset = cached_offset
                return True
            
            # Otherwise, fetch from API
            try:
                api_url = self.config.get("time_api_url")
                
                # Record local time before the request
                local_time_before = time.time()
                
                # Make the request
                response = requests.get(api_url, timeout=5)
                
                # Record local time after the request
                local_time_after = time.time()
                
                if response.status_code != 200:
                    raise APIError(f"Time API returned status code {response.status_code}")
                
                # Parse the response
                data = response.json()
                
                # Calculate the offset
                server_time = data["unixtime"]  # Unix timestamp from the API
                # Use the midpoint of the request for better accuracy
                local_time = (local_time_before + local_time_after) / 2
                
                # Calculate and store the offset
                self._offset = server_time - local_time
                self._last_sync = local_time
                
                # Cache the offset
                cache_duration = self.config.get("time_sync_interval", 300)
                self.cache.set("time_offset", self._offset, cache_duration)
                
                return True
                
            except (requests.RequestException, ValueError, KeyError) as e:
                if not self.config.get("use_fallback", True):
                    raise NetworkError(f"Failed to sync with time API: {str(e)}")
                # If fallback is enabled, continue with local time (offset=0)
                return False
    
    def now(self, timezone: Optional[str] = None, format_as_json: bool = False) -> Union[datetime.datetime, Dict[str, Any]]:
        """Get the current time, using the synchronized offset when available.
        
        Args:
            timezone: Optional timezone name (e.g., 'UTC', 'America/New_York').
                     If None, returns in the UTC timezone.
            format_as_json: Whether to return the result as a JSON structure.
        
        Returns:
            Current datetime in the specified timezone or a JSON structure.
            
        Raises:
            FallbackError: If sync failed and fallback is disabled.
        """
        # If we have a context manager, use it to get the current date
        if self.context_manager:
            dt = self.context_manager.get_current_datetime()
        else:
            # Get the current time with offset
            current_time = time.time() + self._offset
            
            # Convert to datetime
            dt = datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc)
        
        # Convert to specified timezone if requested
        tz_name = timezone or "UTC"
        if timezone and timezone.upper() != 'UTC':
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(timezone)
                dt = dt.astimezone(tz)
            except (ImportError, zoneinfo.ZoneInfoNotFoundError):
                # Fall back to pytz if available
                try:
                    import pytz
                    tz = pytz.timezone(timezone)
                    dt = dt.astimezone(tz)
                except (ImportError, pytz.exceptions.UnknownTimeZoneError):
                    # If timezone conversion fails, return UTC
                    tz_name = "UTC"
                    pass
        
        # If JSON format requested, return a structured response
        if format_as_json:
            response_time = dt.isoformat()
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "time",
                "data": {
                    "datetime": dt.isoformat(),
                    "timezone": tz_name,
                    "unix_timestamp": dt.timestamp(),
                    "day_of_week": dt.strftime("%A"),
                    "day_of_month": dt.day,
                    "month": dt.strftime("%B"),
                    "year": dt.year,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "second": dt.second,
                    "microsecond": dt.microsecond,
                    "is_dst": bool(dt.dst()) if dt.tzinfo else None,
                }
            }
            
            # Add location context if available
            if self.context_manager:
                location = self.context_manager.get_current_location()
                if location:
                    result["location"] = {
                        "name": location.get("name"),
                        "country": location.get("country"),
                    }
            
            return result
        
        # Otherwise return the datetime object
        return dt
    
    @cached(ttl=300)  # Cache for 5 minutes
    def get_timezone_info(self, timezone: str, format_as_json: bool = False) -> Dict[str, Any]:
        """Get information about a timezone.
        
        Args:
            timezone: Timezone name (e.g., 'UTC', 'America/New_York').
            format_as_json: Whether to return the result as a JSON structure.
        
        Returns:
            Dictionary with timezone information.
            
        Raises:
            ValueError: If timezone is invalid.
        """
        try:
            # Try to use zoneinfo (Python 3.9+)
            import zoneinfo
            tz = zoneinfo.ZoneInfo(timezone)
            now = datetime.datetime.now(tz)
            
            timezone_data = {
                "name": timezone,
                "offset": now.utcoffset().total_seconds() / 3600,  # Offset in hours
                "dst": bool(now.dst()),
                "current_time": now.isoformat(),
            }
        except ImportError:
            # Fall back to pytz
            try:
                import pytz
                tz = pytz.timezone(timezone)
                now = datetime.datetime.now(tz)
                
                timezone_data = {
                    "name": timezone,
                    "offset": now.utcoffset().total_seconds() / 3600,  # Offset in hours
                    "dst": bool(now.dst()),
                    "current_time": now.isoformat(),
                }
            except ImportError:
                raise ImportError("Neither zoneinfo nor pytz is available for timezone handling")
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError(f"Invalid timezone: {timezone}")
        
        # If JSON format requested, return a structured response
        if format_as_json:
            response_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if self.context_manager:
                response_time = self.context_manager.get_current_datetime_iso()
            
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "timezone_info",
                "data": timezone_data
            }
            
            # Add location context if available
            if self.context_manager:
                location = self.context_manager.get_current_location()
                if location:
                    result["location"] = {
                        "name": location.get("name"),
                        "country": location.get("country"),
                    }
            
            return result
        
        # Otherwise return the timezone data directly
        return timezone_data
    
    def get_offset(self) -> float:
        """Get the current offset between local time and server time.
        
        Returns:
            Offset in seconds.
        """
        return self._offset
    
    def format_time(self, dt: Optional[datetime.datetime] = None, 
                    fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a datetime object as a string.
        
        Args:
            dt: Datetime to format. If None, uses the current time.
            fmt: Format string (strftime format).
            
        Returns:
            Formatted time string.
        """
        if dt is None:
            dt = self.now()
        
        return dt.strftime(fmt)
    
    def force_sync(self) -> bool:
        """Force a synchronization with the time API.
        
        Returns:
            True if sync was successful, False otherwise.
        """
        return self._sync_time()
