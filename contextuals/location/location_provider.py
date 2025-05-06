"""Location provider for Contextuals."""

import json
import math
import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
import requests

from contextuals.core.cache import Cache, cached
from contextuals.core.config import Config
from contextuals.core.exceptions import APIError, NetworkError, MissingAPIKeyError


class LocationProvider:
    """Provides location-related contextual information.
    
    Features:
    - Geocoding (convert location name to coordinates)
    - Reverse geocoding (convert coordinates to location name)
    - Caches results to minimize API calls
    - Provides fallback data when offline
    """
    
    def __init__(self, config: Config, cache: Cache, context_manager=None):
        """Initialize the location provider.
        
        Args:
            config: Configuration instance.
            cache: Cache instance.
            context_manager: Optional context manager instance.
        """
        self.config = config
        self.cache = cache
        self.context_manager = context_manager
    
    def _get_api_key(self) -> Optional[str]:
        """Get the location API key from configuration.
        
        Returns:
            API key as a string or None if not configured.
            
        Note:
            Some location APIs (like Nominatim) don't require an API key.
        """
        return self.config.get_api_key("location")
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_current_location(self) -> Dict[str, Any]:
        """Get the current location based on IP address.
        
        Returns:
            Current location information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
        """
        # First check if context manager has a location set
        if self.context_manager and self.context_manager.get_current_location():
            return self.context_manager.get_current_location()
        
        # Otherwise, determine location from IP using ip-api.com
        try:
            api_url = "http://ip-api.com/json/"
            
            response = requests.get(api_url, timeout=10)
            
            if response.status_code != 200:
                raise APIError(f"IP location API returned status code {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Check if the API call was successful
            if data.get('status') != 'success':
                raise APIError(f"IP location API returned error: {data.get('message', 'Unknown error')}")
            
            # Extract location data
            location_name = f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}"
            location_name = ", ".join(filter(None, location_name.split(", ")))  # Remove empty parts
            
            # Extract coordinates
            latitude = data.get('lat')
            longitude = data.get('lon')
            
            # Create normalized location data
            location_data = {
                "name": location_name.strip(),
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "address": {
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "city": data.get("city"),
                    "region": data.get("regionName"),
                    "region_code": data.get("region"),
                    "zip": data.get("zip"),
                },
                "type": "administrative",
                "ip": data.get("query"),
                "isp": data.get("isp"),
                "org": data.get("org"),
                "as": data.get("as"),
                "timezone": data.get("timezone"),
            }
            
            # If this is valid, store it in the context manager
            if self.context_manager:
                self.context_manager.set_current_location(location_data)
            
            # Format for consistent return
            response_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            if self.context_manager:
                response_time = self.context_manager.get_current_datetime_iso()
            
            return {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "current_location",
                "is_cached": False,
                "data": location_data
            }
                
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to IP location API: {str(e)}")
    
    def set_current_location(self, location: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Set the current location.
        
        Args:
            location: Location name or location data.
            
        Returns:
            The location data that was set.
        
        Raises:
            Exception: If the location cannot be found.
        """
        # If a string is provided, get the location data
        if isinstance(location, str):
            location_data = self.get(location)
        else:
            location_data = location
        
        # Set the location in the context manager
        if self.context_manager:
            self.context_manager.set_current_location(location_data)
        
        return location_data
    
    @cached(ttl=86400)  # Cache for 24 hours
    def get(self, location: str, format_as_json: bool = False) -> Dict[str, Any]:
        """Get location information by name or address.
        
        Args:
            location: Location name or address.
            format_as_json: Whether to return the result as a JSON structure.
            
        Returns:
            Dictionary with location information.
            
        Raises:
            NetworkError: If API request fails and no fallback is available.
            APIError: If API returns an error.
        """
        try:
            # Attempt to get from API
            location_data = self._geocode(location)
            
            # If this is the only location we have, set it as current
            if self.context_manager and not self.context_manager.get_current_location():
                self.context_manager.set_current_location(location_data)
            
            # Format as JSON if requested
            if format_as_json:
                response_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                if self.context_manager:
                    response_time = self.context_manager.get_current_datetime_iso()
                
                result = {
                    "timestamp": response_time,
                    "request_time": response_time,
                    "type": "location",
                    "is_cached": False,
                    "data": location_data
                }
                return result
            
            return location_data
            
        except (NetworkError, APIError) as e:
            # Check for cached data for fallback
            cached_data = self._get_cached_location(location)
            if cached_data and self.config.get("use_fallback", True):
                # Format as JSON if requested
                if format_as_json:
                    response_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    if self.context_manager:
                        response_time = self.context_manager.get_current_datetime_iso()
                    
                    result = {
                        "timestamp": response_time,
                        "request_time": response_time,
                        "type": "location",
                        "is_cached": True,
                        "data": cached_data
                    }
                    return result
                
                return cached_data
            
            # No fallback available, raise the original error
            raise
    
    def _geocode(self, location: str) -> Dict[str, Any]:
        """Geocode a location name to get coordinates and location data.
        
        Args:
            location: Location name or address.
            
        Returns:
            Dictionary with location information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
        """
        try:
            api_url = self.config.get("location_api_url")
            
            params = {
                "q": location,
                "format": "json",
                "limit": 1,
            }
            
            # Some APIs require an API key
            api_key = self._get_api_key()
            if api_key:
                params["key"] = api_key
            
            headers = {
                "User-Agent": "Contextuals/0.1.0",  # Required for Nominatim
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise APIError(f"Location API returned status code {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Handle empty results
            if not data or (isinstance(data, list) and len(data) == 0):
                raise APIError(f"No location found for: {location}")
            
            # Normalize the response
            result = self._normalize_location_data(data[0] if isinstance(data, list) else data)
            
            # Cache the results for fallback
            cache_key = f"location_{location}"
            self.cache.set(cache_key, result)
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to location API: {str(e)}")
    
    def _normalize_location_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and transform location API response.
        
        Args:
            data: Raw API response.
            
        Returns:
            Normalized location data.
        """
        # Extract coordinates
        lat = data.get("lat") or data.get("latitude")
        lon = data.get("lon") or data.get("longitude")
        
        # Create a normalized representation
        return {
            "name": data.get("display_name") or data.get("name"),
            "coordinates": {
                "latitude": float(lat) if lat else None,
                "longitude": float(lon) if lon else None,
            },
            "address": {
                "country": data.get("address", {}).get("country"),
                "country_code": data.get("address", {}).get("country_code"),
                "state": data.get("address", {}).get("state"),
                "county": data.get("address", {}).get("county"),
                "city": data.get("address", {}).get("city"),
                "postcode": data.get("address", {}).get("postcode"),
            },
            "type": data.get("type") or data.get("category"),
            "importance": data.get("importance"),
            "osm_id": data.get("osm_id"),
        }
    
    def _get_cached_location(self, location: str) -> Optional[Dict[str, Any]]:
        """Get cached location data.
        
        Args:
            location: Location name or address.
            
        Returns:
            Cached location data or None if not found.
        """
        cache_key = f"location_{location}"
        return self.cache.get(cache_key)
    
    @cached(ttl=86400)  # Cache for 24 hours
    def reverse_geocode(self, latitude: float, longitude: float, format_as_json: bool = False) -> Dict[str, Any]:
        """Convert coordinates to a location name and address.
        
        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
            format_as_json: Whether to return the result as a JSON structure.
            
        Returns:
            Dictionary with location information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
        """
        try:
            api_url = self.config.get("location_api_url").replace("search", "reverse")
            
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
            }
            
            # Some APIs require an API key
            api_key = self._get_api_key()
            if api_key:
                params["key"] = api_key
            
            headers = {
                "User-Agent": "Contextuals/0.1.0",  # Required for Nominatim
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise APIError(f"Reverse geocoding API returned status code {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Normalize the response
            location_data = self._normalize_location_data(data)
            
            # If this is the only location we have, set it as current
            if self.context_manager and not self.context_manager.get_current_location():
                self.context_manager.set_current_location(location_data)
            
            # Format as JSON if requested
            if format_as_json:
                response_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                if self.context_manager:
                    response_time = self.context_manager.get_current_datetime_iso()
                
                result = {
                    "timestamp": response_time,
                    "request_time": response_time,
                    "type": "reverse_geocode",
                    "is_cached": False,
                    "data": location_data
                }
                return result
            
            return location_data
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to reverse geocoding API: {str(e)}")
    
    @cached(ttl=86400)  # Cache for 24 hours
    def get_timezone(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get timezone information for coordinates.
        
        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
            
        Returns:
            Dictionary with timezone information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
        """
        # This could use a dedicated timezone API, but for now let's use reverse geocoding
        location_data = self.reverse_geocode(latitude, longitude)
        
        # Extract timezone from location data if available
        timezone = location_data.get("address", {}).get("timezone")
        
        if timezone:
            # If we have timezone data in the response, use it
            return {
                "timezone": timezone,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
            }
        else:
            # Otherwise, we need to use a timezone API or approximate
            from contextuals.time.time_provider import TimeProvider
            time_provider = TimeProvider(self.config, self.cache)
            
            # Get an approximate timezone based on longitude
            # This is a very rough estimate and should be replaced with a proper API
            offset_hours = round(longitude / 15)  # 15 degrees = 1 hour
            
            return {
                "timezone": f"UTC{'+' if offset_hours >= 0 else ''}{offset_hours}",
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "offset_hours": offset_hours,
                "approximate": True,
            }
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "km") -> float:
        """Calculate distance between two coordinates.
        
        Uses the Haversine formula to calculate the great-circle distance.
        
        Args:
            lat1: Latitude of point 1.
            lon1: Longitude of point 1.
            lat2: Latitude of point 2.
            lon2: Longitude of point 2.
            unit: Distance unit ('km' for kilometers or 'mi' for miles).
            
        Returns:
            Distance in the specified unit.
            
        Raises:
            ValueError: If unit is not 'km' or 'mi'.
        """
        from contextuals.location.utils import calculate_haversine_distance
        return calculate_haversine_distance(lat1, lon1, lat2, lon2, unit)
    
    def get_nearby_locations(self, latitude: float, longitude: float, radius: float, 
                            limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find nearby locations within a radius.
        
        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
            radius: Search radius in kilometers.
            limit: Maximum number of results.
            category: Optional category filter (e.g., 'restaurant', 'hotel').
            
        Returns:
            List of nearby locations.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
        """
        try:
            api_url = self.config.get("location_api_url")
            
            params = {
                "format": "json",
                "limit": limit,
            }
            
            # Add category filter if specified
            if category:
                params["amenity"] = category
            
            # Add bounding box
            # Approximate 1 degree of latitude = 111 km
            # Longitude degrees vary with latitude, but let's use a simple approximation
            lat_offset = radius / 111.0
            lon_offset = radius / (111.0 * abs(math.cos(math.radians(latitude))))
            
            params["viewbox"] = f"{longitude - lon_offset},{latitude - lat_offset},{longitude + lon_offset},{latitude + lat_offset}"
            params["bounded"] = 1
            
            # Some APIs require an API key
            api_key = self._get_api_key()
            if api_key:
                params["key"] = api_key
            
            headers = {
                "User-Agent": "Contextuals/0.1.0",  # Required for Nominatim
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                raise APIError(f"Nearby locations API returned status code {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Normalize the response
            results = []
            for item in data:
                location = self._normalize_location_data(item)
                
                # Calculate distance from center point
                location["distance"] = self.calculate_distance(
                    latitude, longitude,
                    location["coordinates"]["latitude"],
                    location["coordinates"]["longitude"]
                )
                
                results.append(location)
            
            # Sort by distance
            results.sort(key=lambda x: x.get("distance", float("inf")))
            
            return results
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to nearby locations API: {str(e)}")
