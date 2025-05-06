"""Weather provider for Contextuals."""

import json
import time
import datetime
from typing import Dict, Any, Optional, List, Union
import requests

from contextuals.core.cache import Cache, cached
from contextuals.core.config import Config
from contextuals.core.exceptions import APIError, NetworkError, MissingAPIKeyError


class WeatherProvider:
    """Provides weather-related contextual information.
    
    Features:
    - Retrieves current weather conditions from a weather API
    - Provides detailed 24-hour forecast
    - Provides 7-day forecast 
    - Provides moon phase information
    - Caches results to minimize API calls
    - Provides fallback data when offline
    - Returns structured JSON responses with timestamps
    """
    
    def __init__(self, config: Config, cache: Cache):
        """Initialize the weather provider.
        
        Args:
            config: Configuration instance.
            cache: Cache instance.
        """
        self.config = config
        self.cache = cache
    
    def _get_api_key(self) -> str:
        """Get the weather API key from configuration.
        
        Returns:
            API key as a string.
            
        Raises:
            MissingAPIKeyError: If API key is not found.
        """
        api_key = self.config.get_api_key("weather")
        if not api_key:
            raise MissingAPIKeyError("weather")
        return api_key
    
    def _get_current_date(self) -> str:
        """Get the current date in ISO format.
        
        This is used to indicate when the data was retrieved.
        
        Returns:
            Current date as string in ISO format.
        """
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    @cached(ttl=300)  # Cache for 5 minutes
    def current(self, location: str) -> Dict[str, Any]:
        """Get current weather conditions for a location.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with weather information.
            
        Raises:
            NetworkError: If API request fails and no fallback is available.
            APIError: If API returns an error.
        """
        response_time = self._get_current_date()
        try:
            # Attempt to get from API
            weather_data = self._fetch_current_weather(location)
            
            # Create the structured response JSON with timestamp
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "current_weather",
                "is_cached": False,
                "location": weather_data["location"],
                "data": weather_data["current"],
            }
            
            # Cache for fallback
            cache_key = f"weather_raw_{location}"
            self.cache.set(cache_key, result)
            
            return result
            
        except (NetworkError, APIError) as e:
            # Check for cached data for fallback
            cached_data = self._get_cached_weather(location)
            if cached_data and self.config.get("use_fallback", True):
                # Add a flag indicating this is stale cached data
                cached_data["is_cached"] = True
                cached_data["fallback_timestamp"] = response_time
                return cached_data
            
            # No fallback available, raise the original error
            raise
    
    def _fetch_current_weather(self, location: str) -> Dict[str, Any]:
        """Fetch current weather from the API.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with weather information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
        """
        try:
            api_key = self._get_api_key()
            api_url = self.config.get("weather_api_url")
            
            params = {
                "appid": api_key,
                "q": location,
                "units": "metric",  # Use metric units (Celsius)
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                error_msg = response.text
                try:
                    # Try to parse the error message for more details
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                except:
                    pass
                raise APIError(f"Weather API returned status code {response.status_code}: {error_msg}")
            
            data = response.json()
            
            # Transform and normalize the response
            return self._normalize_weather_data(data)
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to weather API: {str(e)}")
    
    def _normalize_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and transform weather API response.
        
        Args:
            data: Raw API response from OpenWeatherMap.
            
        Returns:
            Normalized weather data.
        """
        # Extract relevant data from the response
        weather = data.get("weather", [{}])[0]
        main = data.get("main", {})
        wind = data.get("wind", {})
        sys = data.get("sys", {})
        clouds = data.get("clouds", {})
        
        # Convert temperature from Celsius to Fahrenheit
        temp_c = main.get("temp")
        temp_f = None
        if temp_c is not None:
            temp_f = (temp_c * 9/5) + 32
            
        # Convert wind speed from m/s to km/h and mph
        wind_ms = wind.get("speed")
        wind_kph = None
        wind_mph = None
        if wind_ms is not None:
            wind_kph = wind_ms * 3.6  # m/s to km/h
            wind_mph = wind_ms * 2.237  # m/s to mph
            
        # Calculate "is_day" based on sunrise/sunset times
        is_day = None
        if "dt" in data and "sunrise" in sys and "sunset" in sys:
            current_time = data["dt"]
            is_day = current_time > sys["sunrise"] and current_time < sys["sunset"]
        
        # Create a normalized representation matching our standard format
        return {
            "location": {
                "name": data.get("name"),
                "region": "",  # OpenWeatherMap doesn't provide this directly
                "country": sys.get("country"),
                "lat": data.get("coord", {}).get("lat"),
                "lon": data.get("coord", {}).get("lon"),
                "tz_id": None,  # OpenWeatherMap doesn't provide timezone by default
                "localtime": datetime.datetime.fromtimestamp(data.get("dt", 0)).isoformat(),
            },
            "current": {
                "temp_c": temp_c,
                "temp_f": temp_f,
                "is_day": is_day,
                "condition": {
                    "text": weather.get("description"),
                    "code": weather.get("id"),  # OpenWeatherMap uses different condition codes
                },
                "wind_mph": wind_mph,
                "wind_kph": wind_kph,
                "wind_degree": wind.get("deg"),
                "wind_dir": self._get_wind_direction(wind.get("deg")),
                "humidity": main.get("humidity"),
                "cloud": clouds.get("all"),  # Cloud coverage percentage
                "feelslike_c": main.get("feels_like"),
                "feelslike_f": (main.get("feels_like") * 9/5) + 32 if main.get("feels_like") is not None else None,
                "uv": None,  # OpenWeatherMap doesn't provide UV in the basic API
                "pressure": main.get("pressure"),  # Additional data from OpenWeatherMap
                "visibility": data.get("visibility"),  # Visibility in meters
            },
        }
        
    def _get_wind_direction(self, degrees: Optional[float]) -> Optional[str]:
        """Convert wind degrees to cardinal direction.
        
        Args:
            degrees: Wind direction in degrees.
            
        Returns:
            Cardinal direction (e.g., "N", "NE", "E", etc.) or None if degrees is None.
        """
        if degrees is None:
            return None
            
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        
        # Convert degrees to 16-wind compass index
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def _get_cached_weather(self, location: str) -> Optional[Dict[str, Any]]:
        """Get cached weather data for a location.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Cached weather data or None if not found.
        """
        cache_key = f"weather_raw_{location}"
        return self.cache.get(cache_key)
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_air_quality(self, location: str) -> Dict[str, Any]:
        """Get air quality information for a location.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with air quality information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        try:
            # First get coordinates for the location
            location_data = self._get_coordinates(location)
            if not location_data or not location_data.get("lat") or not location_data.get("lon"):
                raise APIError(f"Could not determine coordinates for location: {location}")
                
            lat = location_data["lat"]
            lon = location_data["lon"]
            
            # Now fetch air quality data using coordinates
            api_key = self._get_api_key()
            api_url = self.config.get("weather_air_quality_api_url")
            
            params = {
                "appid": api_key,
                "lat": lat,
                "lon": lon,
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                except:
                    pass
                raise APIError(f"Air quality API returned status code {response.status_code}: {error_msg}")
            
            data = response.json()
            
            # Extract air quality data from OpenWeatherMap response
            air_quality = data.get("list", [{}])[0].get("components", {})
            aqi = data.get("list", [{}])[0].get("main", {}).get("aqi", 0)
            
            # Map AQI value to human-readable description and health implications
            aqi_descriptions = {
                1: "Good",
                2: "Fair",
                3: "Moderate",
                4: "Poor",
                5: "Very Poor"
            }
            
            aqi_health_implications = {
                1: "Air quality is considered satisfactory, and air pollution poses little or no risk.",
                2: "Air quality is acceptable; however, some pollutants may be a concern for a very small number of people who are unusually sensitive to air pollution.",
                3: "Members of sensitive groups may experience health effects. The general public is not likely to be affected.",
                4: "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.",
                5: "Health warnings of emergency conditions. The entire population is more likely to be affected."
            }
            
            # Convert pollution data to health-relevant context
            pollution_context = {}
            
            # WHO guidelines for reference (in μg/m3)
            who_guidelines = {
                "pm2_5": 5,     # Annual mean
                "pm10": 15,     # Annual mean
                "no2": 10,      # Annual mean
                "o3": 100,      # 8-hour mean
                "so2": 40,      # 24-hour mean
                "co": 4000      # 24-hour mean (in μg/m3, converted from 4mg/m3)
            }
            
            # Provide context for each pollutant
            for pollutant, value in air_quality.items():
                if pollutant in who_guidelines and value is not None:
                    guideline = who_guidelines[pollutant]
                    if value <= guideline:
                        status = "Below WHO guideline"
                        risk = "Low"
                    elif value <= guideline * 2:
                        status = "Above WHO guideline"
                        risk = "Moderate"
                    elif value <= guideline * 3.5:
                        status = "Significantly above WHO guideline"
                        risk = "High"
                    else:
                        status = "Dangerously above WHO guideline"
                        risk = "Very High"
                    
                    pollution_context[pollutant] = {
                        "value": value,
                        "unit": "μg/m3",
                        "who_guideline": guideline,
                        "status": status,
                        "health_risk": risk
                    }
            
            # Create structured response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "air_quality",
                "is_cached": False,
                "location": {
                    "name": location,
                    "lat": lat,
                    "lon": lon,
                },
                "data": {
                    # Raw pollution data
                    "pollutants": {
                        "co": air_quality.get("co"),        # Carbon monoxide, μg/m3
                        "o3": air_quality.get("o3"),        # Ozone, μg/m3
                        "no2": air_quality.get("no2"),      # Nitrogen dioxide, μg/m3
                        "so2": air_quality.get("so2"),      # Sulphur dioxide, μg/m3
                        "pm2_5": air_quality.get("pm2_5"),  # Fine particles, μg/m3
                        "pm10": air_quality.get("pm10"),    # Coarse particles, μg/m3
                        "nh3": air_quality.get("nh3"),      # Ammonia, μg/m3 (if available)
                    },
                    # Air Quality Index
                    "aqi": {
                        "value": aqi,  # Air Quality Index (1-5)
                        "description": aqi_descriptions.get(aqi, "Unknown"),
                        "health_implications": aqi_health_implications.get(aqi, "Information not available")
                    },
                    # Health context
                    "health_context": pollution_context,
                    # Recommendations based on AQI
                    "recommendations": self._get_air_quality_recommendations(aqi)
                }
            }
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to air quality API: {str(e)}")
    
    def _get_air_quality_recommendations(self, aqi: int) -> Dict[str, Any]:
        """Get health recommendations based on air quality index.
        
        Args:
            aqi: Air Quality Index (1-5)
            
        Returns:
            Dictionary with recommendations for different groups.
        """
        # Recommendations based on AQI level (from EPA and WHO guidelines)
        if aqi == 1:  # Good
            return {
                "general": "Enjoy your usual outdoor activities.",
                "sensitive_groups": "Enjoy your usual outdoor activities.",
                "outdoor_activity": "Ideal conditions for outdoor activities.",
                "ventilation": "Ideal time for home ventilation."
            }
        elif aqi == 2:  # Fair
            return {
                "general": "Enjoy your usual outdoor activities.",
                "sensitive_groups": "Consider reducing intense outdoor activities if you experience symptoms.",
                "outdoor_activity": "Good conditions for most outdoor activities.",
                "ventilation": "Good time for home ventilation."
            }
        elif aqi == 3:  # Moderate
            return {
                "general": "Consider reducing intense activities outdoors if you experience symptoms like eye irritation or cough.",
                "sensitive_groups": "Consider reducing prolonged or intense activities outdoors. Take more breaks.",
                "outdoor_activity": "Moderate conditions - take breaks and stay hydrated.",
                "ventilation": "Consider limiting home ventilation during peak pollution hours."
            }
        elif aqi == 4:  # Poor
            return {
                "general": "Reduce prolonged or intense activities outdoors. Take more breaks and do less intense activities.",
                "sensitive_groups": "Avoid prolonged or intense activities outdoors. Move activities indoors or reschedule.",
                "outdoor_activity": "Try to limit outdoor exercise. Consider indoor activities instead.",
                "ventilation": "Keep windows closed. Use air purifiers if available."
            }
        elif aqi == 5:  # Very Poor
            return {
                "general": "Avoid prolonged or intense activities outdoors. Move activities indoors or reschedule.",
                "sensitive_groups": "Avoid all outdoor physical activities. Stay indoors and keep activity levels low.",
                "outdoor_activity": "Avoid outdoor exercise. Choose indoor activities.",
                "ventilation": "Keep windows closed. Use air purifiers if available. Consider wearing masks if going outside."
            }
        else:
            return {
                "general": "Information not available. Check local air quality reports.",
                "sensitive_groups": "Information not available. Check local air quality reports.",
                "outdoor_activity": "Information not available.",
                "ventilation": "Information not available."
            }
            
    def _get_coordinates(self, location: str) -> Dict[str, Any]:
        """Get coordinates for a location.
        
        This method first tries to get coordinates from the weather API,
        and falls back to using the location provider if needed.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with "lat" and "lon" keys.
            
        Raises:
            APIError: If coordinates cannot be determined.
        """
        # If location is already in format "lat,lon", parse it
        if "," in location and all(part.strip().replace(".", "").replace("-", "").isdigit() 
                                 for part in location.split(",")):
            lat, lon = location.split(",")
            return {"lat": float(lat.strip()), "lon": float(lon.strip())}
        
        # Try to get location from weather API
        try:
            api_key = self._get_api_key()
            api_url = self.config.get("weather_api_url")
            
            params = {
                "appid": api_key,
                "q": location,
                "units": "metric",
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                coords = data.get("coord", {})
                if coords and "lat" in coords and "lon" in coords:
                    return {"lat": coords["lat"], "lon": coords["lon"]}
        except:
            # If there's any error, we'll try the location provider as fallback
            pass
            
        # If we couldn't get coordinates from weather API, try location provider
        try:
            from contextuals.location.location_provider import LocationProvider
            location_provider = LocationProvider(self.config, self.cache)
            location_data = location_provider.get(location)
            coords = location_data.get("coordinates", {})
            if coords and "latitude" in coords and "longitude" in coords:
                return {"lat": coords["latitude"], "lon": coords["longitude"]}
        except:
            # If location provider fails too, we'll raise an error
            pass
            
        raise APIError(f"Could not determine coordinates for location: {location}")
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_forecast_24h(self, location: str) -> Dict[str, Any]:
        """Get detailed hourly forecast for the next 24 hours.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with hourly forecast information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        try:
            # First get coordinates for the location
            location_data = self._get_coordinates(location)
            if not location_data or not location_data.get("lat") or not location_data.get("lon"):
                raise APIError(f"Could not determine coordinates for location: {location}")
                
            lat = location_data["lat"]
            lon = location_data["lon"]
            
            # Now fetch forecast data using coordinates
            api_key = self._get_api_key()
            api_url = self.config.get("weather_forecast_api_url")
            
            params = {
                "appid": api_key,
                "lat": lat,
                "lon": lon,
                "units": "metric",  # Use metric units (Celsius)
                "cnt": 24,  # Get 24 hours of data (approx)
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", response.text)
                except:
                    pass
                raise APIError(f"Forecast API returned status code {response.status_code}: {error_msg}")
            
            data = response.json()
            
            # Get current time
            now = datetime.datetime.now()
            
            # Extract hourly forecast data
            all_hours = []
            for hour_data in data.get("list", []):
                dt = hour_data.get("dt")  # Unix timestamp
                if not dt:
                    continue
                    
                forecast_time = datetime.datetime.fromtimestamp(dt)
                weather = hour_data.get("weather", [{}])[0]
                main = hour_data.get("main", {})
                wind = hour_data.get("wind", {})
                clouds = hour_data.get("clouds", {})
                pop = hour_data.get("pop", 0)  # Probability of precipitation (0-1)
                
                # Convert temperature from Celsius to Fahrenheit
                temp_c = main.get("temp")
                temp_f = None
                if temp_c is not None:
                    temp_f = (temp_c * 9/5) + 32
                    
                # Convert feels_like from Celsius to Fahrenheit
                feels_like_c = main.get("feels_like")
                feels_like_f = None
                if feels_like_c is not None:
                    feels_like_f = (feels_like_c * 9/5) + 32
                
                # Convert wind speed from m/s to km/h and mph
                wind_ms = wind.get("speed")
                wind_kph = None
                wind_mph = None
                if wind_ms is not None:
                    wind_kph = wind_ms * 3.6  # m/s to km/h
                    wind_mph = wind_ms * 2.237  # m/s to mph
                
                all_hours.append({
                    "time": forecast_time.strftime("%Y-%m-%d %H:%M"),
                    "temp_c": temp_c,
                    "temp_f": temp_f,
                    "condition": {
                        "text": weather.get("description"),
                        "code": weather.get("id"),
                    },
                    "wind_mph": wind_mph,
                    "wind_kph": wind_kph,
                    "wind_degree": wind.get("deg"),
                    "wind_dir": self._get_wind_direction(wind.get("deg")),
                    "humidity": main.get("humidity"),
                    "cloud": clouds.get("all"),
                    "feelslike_c": feels_like_c,
                    "feelslike_f": feels_like_f,
                    "chance_of_rain": int(pop * 100) if weather.get("main") in ["Rain", "Drizzle"] else 0,
                    "chance_of_snow": int(pop * 100) if weather.get("main") == "Snow" else 0,
                    "will_it_rain": 1 if weather.get("main") in ["Rain", "Drizzle"] else 0,
                    "will_it_snow": 1 if weather.get("main") == "Snow" else 0,
                    "pressure": main.get("pressure"),
                    "visibility": hour_data.get("visibility"),
                })
            
            # Create structured response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "forecast_24h",
                "is_cached": False,
                "location": {
                    "name": data.get("city", {}).get("name", location),
                    "country": data.get("city", {}).get("country"),
                    "lat": lat,
                    "lon": lon,
                },
                "data": {
                    "hours": all_hours[:24]  # Limit to 24 hours
                }
            }
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to forecast API: {str(e)}")
    
    @cached(ttl=21600)  # Cache for 6 hours
    def get_forecast_7day(self, location: str) -> Dict[str, Any]:
        """Get weather forecast for 7 days.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with forecast information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        try:
            # First get coordinates for the location
            location_data = self._get_coordinates(location)
            if not location_data or not location_data.get("lat") or not location_data.get("lon"):
                raise APIError(f"Could not determine coordinates for location: {location}")
                
            lat = location_data["lat"]
            lon = location_data["lon"]
            
            # Use OneCAll API for daily forecasts (this requires a different API plan in OpenWeatherMap)
            # Note: Free tier in OpenWeatherMap only supports 5-day forecast
            api_key = self._get_api_key()
            api_url = self.config.get("weather_onecall_api_url")
            
            params = {
                "appid": api_key,
                "lat": lat,
                "lon": lon,
                "units": "metric",  # Use metric units (Celsius)
                "exclude": "current,minutely,hourly,alerts",  # Only get daily forecast
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            # If OneCall API is not available, fall back to 5-day forecast
            if response.status_code != 200:
                # Try the 5-day forecast API instead (this is available on the free tier)
                api_url = self.config.get("weather_forecast_api_url")
                params = {
                    "appid": api_key,
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "cnt": 40,  # Get 5 days of data (8 forecasts per day)
                }
                
                response = requests.get(api_url, params=params, timeout=10)
                
                if response.status_code != 200:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("message", response.text)
                    except:
                        pass
                    raise APIError(f"Forecast API returned status code {response.status_code}: {error_msg}")
                
                # Process 5-day forecast data
                data = response.json()
                forecast_days = self._process_5day_forecast(data)
                max_days = 5  # Free tier only supports 5 days
            else:
                # Process OneCall API data
                data = response.json()
                forecast_days = self._process_onecall_forecast(data)
                max_days = 7
            
            # Create structured response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "forecast_7day",
                "is_cached": False,
                "location": {
                    "name": location,  # We only have coordinates, not location name
                    "lat": lat,
                    "lon": lon,
                },
                "data": {
                    "days": forecast_days[:max_days]
                }
            }
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to forecast API: {str(e)}")
            
    def _process_onecall_forecast(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process daily forecast data from OneCall API.
        
        Args:
            data: Raw API response from OpenWeatherMap OneCall API.
            
        Returns:
            List of daily forecast data.
        """
        forecast_days = []
        for day_data in data.get("daily", []):
            dt = day_data.get("dt")  # Unix timestamp
            if not dt:
                continue
                
            forecast_date = datetime.datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
            weather = day_data.get("weather", [{}])[0]
            temp = day_data.get("temp", {})
            
            # Convert temperatures from Celsius to Fahrenheit
            min_temp_c = temp.get("min")
            max_temp_c = temp.get("max")
            day_temp_c = temp.get("day")
            
            min_temp_f = None
            max_temp_f = None
            day_temp_f = None
            
            if min_temp_c is not None:
                min_temp_f = (min_temp_c * 9/5) + 32
            if max_temp_c is not None:
                max_temp_f = (max_temp_c * 9/5) + 32
            if day_temp_c is not None:
                day_temp_f = (day_temp_c * 9/5) + 32
            
            # Precipitation probabilities
            pop = day_data.get("pop", 0)  # Probability of precipitation (0-1)
            
            forecast_days.append({
                "date": forecast_date,
                "max_temp_c": max_temp_c,
                "min_temp_c": min_temp_c,
                "avg_temp_c": day_temp_c,
                "max_temp_f": max_temp_f,
                "min_temp_f": min_temp_f,
                "avg_temp_f": day_temp_f,
                "condition": {
                    "text": weather.get("description"),
                    "code": weather.get("id"),
                },
                "uv": day_data.get("uvi"),
                "chance_of_rain": int(pop * 100) if weather.get("main") in ["Rain", "Drizzle"] else 0,
                "chance_of_snow": int(pop * 100) if weather.get("main") == "Snow" else 0,
                "totalprecip_mm": day_data.get("rain", 0),  # Rain in mm
                "totalprecip_in": day_data.get("rain", 0) / 25.4 if day_data.get("rain") is not None else None,  # Convert mm to inches
                "avghumidity": day_data.get("humidity"),
                "daily_will_it_rain": 1 if weather.get("main") in ["Rain", "Drizzle"] else 0,
                "daily_will_it_snow": 1 if weather.get("main") == "Snow" else 0,
            })
        
        return forecast_days
    
    def _process_5day_forecast(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process daily forecast data from 5-day forecast API.
        
        This method aggregates 3-hour forecasts into daily forecasts.
        
        Args:
            data: Raw API response from OpenWeatherMap 5-day forecast API.
            
        Returns:
            List of daily forecast data.
        """
        # Group forecast data by day
        days = {}
        for hour_data in data.get("list", []):
            dt = hour_data.get("dt")  # Unix timestamp
            if not dt:
                continue
                
            date = datetime.datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
            if date not in days:
                days[date] = []
            days[date].append(hour_data)
        
        # Aggregate data for each day
        forecast_days = []
        for date, hours in sorted(days.items()):
            # Calculate min, max, and avg temperatures
            temps = [hour.get("main", {}).get("temp") for hour in hours if hour.get("main", {}).get("temp") is not None]
            if not temps:
                continue
                
            min_temp_c = min(temps)
            max_temp_c = max(temps)
            avg_temp_c = sum(temps) / len(temps)
            
            # Convert to Fahrenheit
            min_temp_f = (min_temp_c * 9/5) + 32
            max_temp_f = (max_temp_c * 9/5) + 32
            avg_temp_f = (avg_temp_c * 9/5) + 32
            
            # Count precipitation types
            rain_count = sum(1 for hour in hours if any(w.get("main") in ["Rain", "Drizzle"] for w in hour.get("weather", [])))
            snow_count = sum(1 for hour in hours if any(w.get("main") == "Snow" for w in hour.get("weather", [])))
            
            # Get the most common weather condition
            all_weather = []
            for hour in hours:
                for w in hour.get("weather", []):
                    all_weather.append(w)
            
            if not all_weather:
                continue
                
            # Use the most common condition (simplified approach)
            weather = all_weather[0]
            
            # Calculate average pop (probability of precipitation)
            pops = [hour.get("pop", 0) for hour in hours]
            avg_pop = sum(pops) / len(pops) if pops else 0
            
            # Calculate total precipitation
            total_rain = sum(hour.get("rain", {}).get("3h", 0) for hour in hours)
            
            # Calculate average humidity
            humidity = [hour.get("main", {}).get("humidity") for hour in hours if hour.get("main", {}).get("humidity") is not None]
            avg_humidity = sum(humidity) / len(humidity) if humidity else None
            
            forecast_days.append({
                "date": date,
                "max_temp_c": max_temp_c,
                "min_temp_c": min_temp_c,
                "avg_temp_c": avg_temp_c,
                "max_temp_f": max_temp_f,
                "min_temp_f": min_temp_f,
                "avg_temp_f": avg_temp_f,
                "condition": {
                    "text": weather.get("description"),
                    "code": weather.get("id"),
                },
                "uv": None,  # Not available in 5-day forecast
                "chance_of_rain": int(avg_pop * 100) if rain_count > 0 else 0,
                "chance_of_snow": int(avg_pop * 100) if snow_count > 0 else 0,
                "totalprecip_mm": total_rain,
                "totalprecip_in": total_rain / 25.4 if total_rain is not None else None,
                "avghumidity": avg_humidity,
                "daily_will_it_rain": 1 if rain_count > 0 else 0,
                "daily_will_it_snow": 1 if snow_count > 0 else 0,
            })
        
        return forecast_days
    
    @cached(ttl=86400)  # Cache for 24 hours
    def get_moon_phases(self, location: str, days: int = 7) -> Dict[str, Any]:
        """Get moon phase information for a specified number of days.
        
        Note: OpenWeatherMap doesn't directly provide moon phase data in the free tier.
        This method calculates moon phases based on date using a simple algorithm.
        
        Args:
            location: Location name or coordinates.
            days: Number of days to get moon phases for (1-30).
            
        Returns:
            Dictionary with moon phase information.
            
        Raises:
            ValueError: If days is not between 1 and 30.
        """
        if not 1 <= days <= 30:
            raise ValueError("Moon phase days must be between 1 and 30")
        
        response_time = self._get_current_date()
        
        # First get coordinates for the location for proper sunrise/sunset times
        try:
            location_data = self._get_coordinates(location)
            if not location_data or not location_data.get("lat") or not location_data.get("lon"):
                raise APIError(f"Could not determine coordinates for location: {location}")
                
            lat = location_data["lat"]
            lon = location_data["lon"]
            
            # Try to use OneCall API to get proper sunrise/sunset times
            # Note: This requires a paid tier for OpenWeatherMap
            try:
                api_key = self._get_api_key()
                api_url = self.config.get("weather_onecall_api_url")
                
                params = {
                    "appid": api_key,
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "exclude": "current,minutely,hourly,alerts",
                }
                
                response = requests.get(api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    moon_data = self._process_moon_data_from_onecall(data, days)
                else:
                    # If OneCall isn't available, calculate approximate moon data
                    moon_data = self._calculate_moon_data(days, lat, lon)
            except:
                # If API fails, fall back to calculation
                moon_data = self._calculate_moon_data(days, lat, lon)
                
            # Create structured response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "moon_phases",
                "is_cached": False,
                "location": {
                    "name": location,
                    "lat": lat,
                    "lon": lon,
                },
                "data": {
                    "phases": moon_data
                }
            }
            
            return result
            
        except:
            # If all else fails, provide calculated moon data without location
            moon_data = self._calculate_moon_data(days)
            
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "moon_phases",
                "is_cached": False,
                "location": {
                    "name": location,
                },
                "data": {
                    "phases": moon_data
                }
            }
            
            return result
            
    def _process_moon_data_from_onecall(self, data: Dict[str, Any], days: int) -> List[Dict[str, Any]]:
        """Extract moon data from OneCall API response.
        
        Args:
            data: OneCall API response.
            days: Number of days.
            
        Returns:
            List of moon data dictionaries.
        """
        moon_data = []
        for day_data in data.get("daily", [])[:days]:
            dt = day_data.get("dt")  # Unix timestamp
            if not dt:
                continue
                
            date = datetime.datetime.fromtimestamp(dt).strftime("%Y-%m-%d")
            
            # Extract moonrise/moonset and sunrise/sunset
            moonrise = day_data.get("moonrise")
            moonset = day_data.get("moonset")
            sunrise = day_data.get("sunrise")
            sunset = day_data.get("sunset")
            
            # Format times
            moonrise_str = datetime.datetime.fromtimestamp(moonrise).strftime("%H:%M") if moonrise else "Unknown"
            moonset_str = datetime.datetime.fromtimestamp(moonset).strftime("%H:%M") if moonset else "Unknown"
            sunrise_str = datetime.datetime.fromtimestamp(sunrise).strftime("%H:%M") if sunrise else "Unknown"
            sunset_str = datetime.datetime.fromtimestamp(sunset).strftime("%H:%M") if sunset else "Unknown"
            
            # Get moon phase information
            moon_phase = day_data.get("moon_phase", 0)  # 0 = New Moon, 0.25 = First Quarter, 0.5 = Full Moon, 0.75 = Last Quarter
            
            # Convert to string description
            if 0 <= moon_phase < 0.03 or moon_phase > 0.97:
                phase_str = "New Moon"
            elif 0.03 <= moon_phase < 0.22:
                phase_str = "Waxing Crescent"
            elif 0.22 <= moon_phase < 0.28:
                phase_str = "First Quarter"
            elif 0.28 <= moon_phase < 0.47:
                phase_str = "Waxing Gibbous"
            elif 0.47 <= moon_phase < 0.53:
                phase_str = "Full Moon"
            elif 0.53 <= moon_phase < 0.72:
                phase_str = "Waning Gibbous"
            elif 0.72 <= moon_phase < 0.78:
                phase_str = "Last Quarter"
            else:
                phase_str = "Waning Crescent"
            
            # Calculate moon illumination (approximation)
            illumination = abs(50 - abs(moon_phase * 100 - 50)) * 2
            
            moon_data.append({
                "date": date,
                "moon_phase": phase_str,
                "moon_illumination": str(int(illumination)),
                "moonrise": moonrise_str,
                "moonset": moonset_str,
                "sunrise": sunrise_str,
                "sunset": sunset_str,
            })
            
        return moon_data
        
    def _calculate_moon_data(self, days: int, lat: float = None, lon: float = None) -> List[Dict[str, Any]]:
        """Calculate approximate moon data without API.
        
        Args:
            days: Number of days.
            lat: Optional latitude for sunrise/sunset calculations.
            lon: Optional longitude for sunrise/sunset calculations.
            
        Returns:
            List of moon data dictionaries.
        """
        moon_data = []
        
        # New Moon date - Jan 2, 2022 as reference
        reference_new_moon = datetime.datetime(2022, 1, 2)
        lunar_cycle = 29.53  # Days in lunar cycle
        
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(days):
            date = today + datetime.timedelta(days=i)
            
            # Calculate days since reference new moon
            days_since_new = (date - reference_new_moon).total_seconds() / (24 * 3600)
            
            # Calculate position in lunar cycle (0 to 1)
            position = (days_since_new % lunar_cycle) / lunar_cycle
            
            # Determine phase name
            if 0 <= position < 0.03 or position > 0.97:
                phase_str = "New Moon"
            elif 0.03 <= position < 0.22:
                phase_str = "Waxing Crescent"
            elif 0.22 <= position < 0.28:
                phase_str = "First Quarter"
            elif 0.28 <= position < 0.47:
                phase_str = "Waxing Gibbous"
            elif 0.47 <= position < 0.53:
                phase_str = "Full Moon"
            elif 0.53 <= position < 0.72:
                phase_str = "Waning Gibbous"
            elif 0.72 <= position < 0.78:
                phase_str = "Last Quarter"
            else:
                phase_str = "Waning Crescent"
            
            # Calculate illumination (approximation)
            illumination = abs(50 - abs(position * 100 - 50)) * 2
            
            # Add approximate sunrise/sunset times based on latitude if available
            sunrise_str = "06:00"
            sunset_str = "18:00"
            moonrise_str = "Unknown"
            moonset_str = "Unknown"
            
            # Better approximation with latitude if available (very simplified)
            if lat is not None:
                # Seasonal adjustment (very approximate)
                day_of_year = date.timetuple().tm_yday
                seasonal_adjustment = abs(day_of_year - 183) / 182.0  # 0 at equinox, 1 at solstice
                
                # Northern hemisphere
                if lat > 0:
                    if day_of_year < 183:  # First half of year
                        sunrise_str = f"{6 - int(seasonal_adjustment * lat / 15)}:00"
                        sunset_str = f"{18 + int(seasonal_adjustment * lat / 15)}:00"
                    else:  # Second half of year
                        sunrise_str = f"{6 + int(seasonal_adjustment * lat / 15)}:00"
                        sunset_str = f"{18 - int(seasonal_adjustment * lat / 15)}:00"
                # Southern hemisphere
                else:
                    if day_of_year < 183:  # First half of year
                        sunrise_str = f"{6 + int(seasonal_adjustment * abs(lat) / 15)}:00"
                        sunset_str = f"{18 - int(seasonal_adjustment * abs(lat) / 15)}:00"
                    else:  # Second half of year
                        sunrise_str = f"{6 - int(seasonal_adjustment * abs(lat) / 15)}:00"
                        sunset_str = f"{18 + int(seasonal_adjustment * abs(lat) / 15)}:00"
            
            moon_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "moon_phase": phase_str,
                "moon_illumination": str(int(illumination)),
                "moonrise": moonrise_str,
                "moonset": moonset_str,
                "sunrise": sunrise_str,
                "sunset": sunset_str,
            })
            
        return moon_data
    
    def interpret_condition(self, condition_code: int) -> str:
        """Interpret a weather condition code.
        
        Args:
            condition_code: Weather condition code from OpenWeatherMap API.
            
        Returns:
            Human-readable description of the condition.
        """
        # Mapping of OpenWeatherMap condition codes to human-readable descriptions
        # Based on OpenWeatherMap API documentation
        condition_map = {
            # Group 2xx: Thunderstorm
            200: "Thunderstorm with light rain",
            201: "Thunderstorm with rain",
            202: "Thunderstorm with heavy rain",
            210: "Light thunderstorm",
            211: "Thunderstorm",
            212: "Heavy thunderstorm",
            221: "Ragged thunderstorm",
            230: "Thunderstorm with light drizzle",
            231: "Thunderstorm with drizzle",
            232: "Thunderstorm with heavy drizzle",
            
            # Group 3xx: Drizzle
            300: "Light intensity drizzle",
            301: "Drizzle",
            302: "Heavy intensity drizzle",
            310: "Light intensity drizzle rain",
            311: "Drizzle rain",
            312: "Heavy intensity drizzle rain",
            313: "Shower rain and drizzle",
            314: "Heavy shower rain and drizzle",
            321: "Shower drizzle",
            
            # Group 5xx: Rain
            500: "Light rain",
            501: "Moderate rain",
            502: "Heavy intensity rain",
            503: "Very heavy rain",
            504: "Extreme rain",
            511: "Freezing rain",
            520: "Light intensity shower rain",
            521: "Shower rain",
            522: "Heavy intensity shower rain",
            531: "Ragged shower rain",
            
            # Group 6xx: Snow
            600: "Light snow",
            601: "Snow",
            602: "Heavy snow",
            611: "Sleet",
            612: "Light shower sleet",
            613: "Shower sleet",
            615: "Light rain and snow",
            616: "Rain and snow",
            620: "Light shower snow",
            621: "Shower snow",
            622: "Heavy shower snow",
            
            # Group 7xx: Atmosphere
            701: "Mist",
            711: "Smoke",
            721: "Haze",
            731: "Sand/dust whirls",
            741: "Fog",
            751: "Sand",
            761: "Dust",
            762: "Volcanic ash",
            771: "Squalls",
            781: "Tornado",
            
            # Group 800: Clear
            800: "Clear sky",
            
            # Group 80x: Clouds
            801: "Few clouds (11-25%)",
            802: "Scattered clouds (25-50%)",
            803: "Broken clouds (51-84%)",
            804: "Overcast clouds (85-100%)",
        }
        
        return condition_map.get(condition_code, "Unknown condition")
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_astronomy(self, location: str) -> Dict[str, Any]:
        """Get astronomical data for a location.
        
        This includes sunrise, sunset, moonrise, moonset, and twilight times.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with astronomical information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        try:
            # First get coordinates for the location
            location_data = self._get_coordinates(location)
            if not location_data or not location_data.get("lat") or not location_data.get("lon"):
                raise APIError(f"Could not determine coordinates for location: {location}")
                
            lat = location_data["lat"]
            lon = location_data["lon"]
            
            # Try to use OneCall API for complete astro data
            # Note: This requires a paid tier for OpenWeatherMap
            try:
                api_key = self._get_api_key()
                api_url = self.config.get("weather_onecall_api_url")
                
                params = {
                    "appid": api_key,
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "exclude": "minutely,hourly,alerts",  # Keep daily and current
                }
                
                response = requests.get(api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    astro_data = self._process_astro_data_from_onecall(data)
                else:
                    # If OneCall isn't available, fall back to current weather
                    astro_data = self._get_basic_astro_data(lat, lon)
            except:
                # If API fails, fall back to basic data
                astro_data = self._get_basic_astro_data(lat, lon)
                
            # Create structured response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "astronomy",
                "is_cached": False,
                "location": {
                    "name": location,
                    "lat": lat,
                    "lon": lon,
                },
                "data": astro_data
            }
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to astronomy API: {str(e)}")
    
    def _process_astro_data_from_onecall(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process astronomical data from OneCall API.
        
        Args:
            data: OneCall API response.
            
        Returns:
            Dictionary with processed astronomical data.
        """
        # Extract current data
        current = data.get("current", {})
        daily = data.get("daily", [{}])[0] if data.get("daily") else {}
        
        # Get sunrise and sunset times
        sunrise = current.get("sunrise")
        sunset = current.get("sunset")
        
        # Format times
        sunrise_dt = datetime.datetime.fromtimestamp(sunrise) if sunrise else None
        sunset_dt = datetime.datetime.fromtimestamp(sunset) if sunset else None
        
        # Calculate day length
        day_length = None
        if sunrise_dt and sunset_dt:
            day_length_seconds = (sunset_dt - sunrise_dt).total_seconds()
            hours = int(day_length_seconds // 3600)
            minutes = int((day_length_seconds % 3600) // 60)
            day_length = f"{hours:02d}:{minutes:02d}"
        
        # Get moonrise and moonset if available
        moonrise = daily.get("moonrise")
        moonset = daily.get("moonset")
        
        # Format moon times
        moonrise_dt = datetime.datetime.fromtimestamp(moonrise) if moonrise else None
        moonset_dt = datetime.datetime.fromtimestamp(moonset) if moonset else None
        
        # Calculate twilight times (civil twilight is approx. 30 minutes before sunrise and after sunset)
        civil_twilight_begin = None
        civil_twilight_end = None
        
        if sunrise_dt:
            civil_twilight_begin = sunrise_dt - datetime.timedelta(minutes=30)
        if sunset_dt:
            civil_twilight_end = sunset_dt + datetime.timedelta(minutes=30)
        
        # Compile all data
        return {
            "sun": {
                "sunrise": sunrise_dt.strftime("%H:%M:%S") if sunrise_dt else None,
                "sunset": sunset_dt.strftime("%H:%M:%S") if sunset_dt else None,
                "day_length": day_length,
                "civil_twilight": {
                    "begin": civil_twilight_begin.strftime("%H:%M:%S") if civil_twilight_begin else None,
                    "end": civil_twilight_end.strftime("%H:%M:%S") if civil_twilight_end else None,
                }
            },
            "moon": {
                "moonrise": moonrise_dt.strftime("%H:%M:%S") if moonrise_dt else None,
                "moonset": moonset_dt.strftime("%H:%M:%S") if moonset_dt else None,
                "phase": daily.get("moon_phase", None),
                "phase_description": self._get_moon_phase_description(daily.get("moon_phase", None)),
                "illumination": self._calculate_moon_illumination(daily.get("moon_phase", None)),
            }
        }
    
    def _get_basic_astro_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get basic astronomical data using standard weather API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with basic astronomical data.
        """
        try:
            api_key = self._get_api_key()
            api_url = self.config.get("weather_api_url")
            
            params = {
                "appid": api_key,
                "lat": lat,
                "lon": lon,
                "units": "metric",
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract sunrise and sunset times
                sys = data.get("sys", {})
                sunrise = sys.get("sunrise")
                sunset = sys.get("sunset")
                
                # Format times
                sunrise_dt = datetime.datetime.fromtimestamp(sunrise) if sunrise else None
                sunset_dt = datetime.datetime.fromtimestamp(sunset) if sunset else None
                
                # Calculate day length
                day_length = None
                if sunrise_dt and sunset_dt:
                    day_length_seconds = (sunset_dt - sunrise_dt).total_seconds()
                    hours = int(day_length_seconds // 3600)
                    minutes = int((day_length_seconds % 3600) // 60)
                    day_length = f"{hours:02d}:{minutes:02d}"
                
                # Calculate twilight times (civil twilight is approx. 30 minutes before sunrise and after sunset)
                civil_twilight_begin = None
                civil_twilight_end = None
                
                if sunrise_dt:
                    civil_twilight_begin = sunrise_dt - datetime.timedelta(minutes=30)
                if sunset_dt:
                    civil_twilight_end = sunset_dt + datetime.timedelta(minutes=30)
                
                # For moon data, we'll use our calculation function since the basic API doesn't have it
                today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                moon_position = self._calculate_moon_position(today)
                
                return {
                    "sun": {
                        "sunrise": sunrise_dt.strftime("%H:%M:%S") if sunrise_dt else None,
                        "sunset": sunset_dt.strftime("%H:%M:%S") if sunset_dt else None,
                        "day_length": day_length,
                        "civil_twilight": {
                            "begin": civil_twilight_begin.strftime("%H:%M:%S") if civil_twilight_begin else None,
                            "end": civil_twilight_end.strftime("%H:%M:%S") if civil_twilight_end else None,
                        }
                    },
                    "moon": {
                        "moonrise": "Unknown",  # Not available in basic API
                        "moonset": "Unknown",  # Not available in basic API
                        "phase": moon_position,
                        "phase_description": self._get_moon_phase_description(moon_position),
                        "illumination": self._calculate_moon_illumination(moon_position),
                    }
                }
            else:
                # If API call fails, return very basic calculated data
                return self._calculate_astronomical_data(lat, lon)
        except:
            # Fall back to calculated data
            return self._calculate_astronomical_data(lat, lon)
    
    def _calculate_astronomical_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Calculate basic astronomical data when API data is not available.
        
        This uses a very simplified model and should only be used as a fallback.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with calculated astronomical data.
        """
        # Current date
        now = datetime.datetime.now()
        day_of_year = now.timetuple().tm_yday
        
        # Approximate sunrise/sunset calculation (very simplified)
        # Base times (these vary by latitude and season)
        base_sunrise = datetime.datetime(now.year, now.month, now.day, 6, 0, 0)
        base_sunset = datetime.datetime(now.year, now.month, now.day, 18, 0, 0)
        
        # Adjust for latitude and season (very approximate)
        seasonal_adjustment = abs(day_of_year - 183) / 182.0  # 0 at equinox, 1 at solstice
        latitude_factor = abs(lat) / 90.0  # 0 at equator, 1 at poles
        
        # Calculate minutes of adjustment
        adjustment_minutes = int(seasonal_adjustment * latitude_factor * 180)  # up to 3 hours
        
        # Apply the adjustment
        if lat > 0:  # Northern hemisphere
            if day_of_year < 183:  # First half of year
                sunrise = base_sunrise - datetime.timedelta(minutes=adjustment_minutes)
                sunset = base_sunset + datetime.timedelta(minutes=adjustment_minutes)
            else:  # Second half of year
                sunrise = base_sunrise + datetime.timedelta(minutes=adjustment_minutes)
                sunset = base_sunset - datetime.timedelta(minutes=adjustment_minutes)
        else:  # Southern hemisphere
            if day_of_year < 183:  # First half of year
                sunrise = base_sunrise + datetime.timedelta(minutes=adjustment_minutes)
                sunset = base_sunset - datetime.timedelta(minutes=adjustment_minutes)
            else:  # Second half of year
                sunrise = base_sunrise - datetime.timedelta(minutes=adjustment_minutes)
                sunset = base_sunset + datetime.timedelta(minutes=adjustment_minutes)
        
        # Calculate day length
        day_length_seconds = (sunset - sunrise).total_seconds()
        hours = int(day_length_seconds // 3600)
        minutes = int((day_length_seconds % 3600) // 60)
        day_length = f"{hours:02d}:{minutes:02d}"
        
        # Calculate twilight times
        civil_twilight_begin = sunrise - datetime.timedelta(minutes=30)
        civil_twilight_end = sunset + datetime.timedelta(minutes=30)
        
        # Get moon phase using our calculation
        moon_position = self._calculate_moon_position(now)
        
        return {
            "sun": {
                "sunrise": sunrise.strftime("%H:%M:%S"),
                "sunset": sunset.strftime("%H:%M:%S"),
                "day_length": day_length,
                "civil_twilight": {
                    "begin": civil_twilight_begin.strftime("%H:%M:%S"),
                    "end": civil_twilight_end.strftime("%H:%M:%S"),
                }
            },
            "moon": {
                "moonrise": "Unknown",  # Not easily calculable without complex algorithms
                "moonset": "Unknown",  # Not easily calculable without complex algorithms
                "phase": moon_position,
                "phase_description": self._get_moon_phase_description(moon_position),
                "illumination": self._calculate_moon_illumination(moon_position),
            },
            "note": "This data is calculated using a simplified model and may not be accurate."
        }
    
    def _calculate_moon_position(self, date: datetime.datetime) -> float:
        """Calculate position in lunar cycle (0 to 1).
        
        Args:
            date: The date to calculate for.
            
        Returns:
            Moon position between 0 and 1 (0 = New Moon, 0.5 = Full Moon).
        """
        # New Moon date - Jan 2, 2022 as reference
        reference_new_moon = datetime.datetime(2022, 1, 2)
        lunar_cycle = 29.53  # Days in lunar cycle
        
        # Calculate days since reference new moon
        days_since_new = (date - reference_new_moon).total_seconds() / (24 * 3600)
        
        # Calculate position in lunar cycle (0 to 1)
        position = (days_since_new % lunar_cycle) / lunar_cycle
        
        return position
    
    def _get_moon_phase_description(self, position: Optional[float]) -> Optional[str]:
        """Get moon phase description based on position in lunar cycle.
        
        Args:
            position: Position in lunar cycle (0 to 1).
            
        Returns:
            Moon phase description or None if position is None.
        """
        if position is None:
            return None
            
        if 0 <= position < 0.03 or position > 0.97:
            return "New Moon"
        elif 0.03 <= position < 0.22:
            return "Waxing Crescent"
        elif 0.22 <= position < 0.28:
            return "First Quarter"
        elif 0.28 <= position < 0.47:
            return "Waxing Gibbous"
        elif 0.47 <= position < 0.53:
            return "Full Moon"
        elif 0.53 <= position < 0.72:
            return "Waning Gibbous"
        elif 0.72 <= position < 0.78:
            return "Last Quarter"
        else:
            return "Waning Crescent"
    
    def _calculate_moon_illumination(self, position: Optional[float]) -> Optional[int]:
        """Calculate moon illumination percentage based on position in lunar cycle.
        
        Args:
            position: Position in lunar cycle (0 to 1).
            
        Returns:
            Illumination percentage (0-100) or None if position is None.
        """
        if position is None:
            return None
            
        # Simplified calculation - illumination follows a sine wave pattern
        # 0 = New Moon (0% illumination), 0.5 = Full Moon (100% illumination)
        return int(abs(50 - abs(position * 100 - 50)) * 2)
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_detailed_weather(self, location: str) -> Dict[str, Any]:
        """Get extended weather details including UV index, visibility, and pressure.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with extended weather information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        try:
            # First get coordinates for the location
            location_data = self._get_coordinates(location)
            if not location_data or not location_data.get("lat") or not location_data.get("lon"):
                raise APIError(f"Could not determine coordinates for location: {location}")
                
            lat = location_data["lat"]
            lon = location_data["lon"]
            
            # Try to use OneCall API for complete data
            # Note: This requires a paid tier for OpenWeatherMap
            try:
                api_key = self._get_api_key()
                api_url = self.config.get("weather_onecall_api_url")
                
                params = {
                    "appid": api_key,
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "exclude": "minutely,hourly,alerts",  # Keep daily and current
                }
                
                response = requests.get(api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    detailed_data = self._process_detailed_data_from_onecall(data)
                else:
                    # If OneCall isn't available, fall back to current weather
                    detailed_data = self._get_basic_detailed_data(lat, lon)
            except:
                # If API fails, fall back to basic data
                detailed_data = self._get_basic_detailed_data(lat, lon)
                
            # Create structured response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "detailed_weather",
                "is_cached": False,
                "location": {
                    "name": location,
                    "lat": lat,
                    "lon": lon,
                },
                "data": detailed_data
            }
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to weather API: {str(e)}")
    
    def _process_detailed_data_from_onecall(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process detailed weather data from OneCall API.
        
        Args:
            data: OneCall API response.
            
        Returns:
            Dictionary with processed detailed weather data.
        """
        # Extract current data
        current = data.get("current", {})
        
        # Extract UV index
        uvi = current.get("uvi")
        
        # Extract pressure
        pressure = current.get("pressure")
        
        # Extract visibility (convert from meters to km)
        visibility_meters = current.get("visibility", 0)
        visibility_km = visibility_meters / 1000 if visibility_meters else None
        
        # Extract humidity
        humidity = current.get("humidity")
        
        # Extract dew point
        dew_point = current.get("dew_point")
        
        # Process additional data
        return {
            "uv_index": {
                "value": uvi,
                "category": self._get_uv_category(uvi),
                "risk_level": self._get_uv_risk(uvi),
                "protection_required": self._get_uv_protection_advice(uvi)
            },
            "visibility": {
                "meters": visibility_meters,
                "kilometers": visibility_km,
                "description": self._get_visibility_description(visibility_km if visibility_km is not None else 0)
            },
            "pressure": {
                "value": pressure,
                "unit": "hPa",
                "description": self._get_pressure_description(pressure if pressure is not None else 0)
            },
            "humidity": {
                "value": humidity,
                "unit": "%",
                "comfort_level": self._get_humidity_comfort(humidity if humidity is not None else 0)
            },
            "dew_point": {
                "value": dew_point,
                "unit": "°C",
                "description": self._get_dew_point_description(dew_point if dew_point is not None else 0)
            }
        }
    
    def _get_basic_detailed_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get basic detailed weather data using standard weather API.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with basic detailed weather data.
        """
        try:
            api_key = self._get_api_key()
            api_url = self.config.get("weather_api_url")
            
            params = {
                "appid": api_key,
                "lat": lat,
                "lon": lon,
                "units": "metric",
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract available data
                main = data.get("main", {})
                
                # Extract pressure
                pressure = main.get("pressure")
                
                # Extract visibility (convert from meters to km)
                visibility_meters = data.get("visibility", 0)
                visibility_km = visibility_meters / 1000 if visibility_meters else None
                
                # Extract humidity
                humidity = main.get("humidity")
                
                # Note: UV index and dew point not available in basic API
                
                return {
                    "uv_index": {
                        "value": None,
                        "category": "Unknown",
                        "risk_level": "Unknown",
                        "protection_required": "Use general sun protection as a precaution."
                    },
                    "visibility": {
                        "meters": visibility_meters,
                        "kilometers": visibility_km,
                        "description": self._get_visibility_description(visibility_km if visibility_km is not None else 0)
                    },
                    "pressure": {
                        "value": pressure,
                        "unit": "hPa",
                        "description": self._get_pressure_description(pressure if pressure is not None else 0)
                    },
                    "humidity": {
                        "value": humidity,
                        "unit": "%",
                        "comfort_level": self._get_humidity_comfort(humidity if humidity is not None else 0)
                    },
                    "dew_point": {
                        "value": None,
                        "unit": "°C",
                        "description": "Information not available"
                    }
                }
            else:
                # Return empty data if API fails
                return {
                    "uv_index": {"value": None, "category": "Unknown", "risk_level": "Unknown", "protection_required": "Unknown"},
                    "visibility": {"meters": None, "kilometers": None, "description": "Unknown"},
                    "pressure": {"value": None, "unit": "hPa", "description": "Unknown"},
                    "humidity": {"value": None, "unit": "%", "comfort_level": "Unknown"},
                    "dew_point": {"value": None, "unit": "°C", "description": "Unknown"}
                }
        except:
            # Return empty data if API fails
            return {
                "uv_index": {"value": None, "category": "Unknown", "risk_level": "Unknown", "protection_required": "Unknown"},
                "visibility": {"meters": None, "kilometers": None, "description": "Unknown"},
                "pressure": {"value": None, "unit": "hPa", "description": "Unknown"},
                "humidity": {"value": None, "unit": "%", "comfort_level": "Unknown"},
                "dew_point": {"value": None, "unit": "°C", "description": "Unknown"}
            }
    
    def _get_uv_category(self, uvi: Optional[float]) -> str:
        """Get UV index category based on value.
        
        Args:
            uvi: UV index value
            
        Returns:
            Category description
        """
        if uvi is None:
            return "Unknown"
            
        if uvi < 3:
            return "Low"
        elif uvi < 6:
            return "Moderate"
        elif uvi < 8:
            return "High"
        elif uvi < 11:
            return "Very High"
        else:
            return "Extreme"
    
    def _get_uv_risk(self, uvi: Optional[float]) -> str:
        """Get UV index risk level based on value.
        
        Args:
            uvi: UV index value
            
        Returns:
            Risk description
        """
        if uvi is None:
            return "Unknown"
            
        if uvi < 3:
            return "Low risk of harm from unprotected sun exposure"
        elif uvi < 6:
            return "Moderate risk of harm from unprotected sun exposure"
        elif uvi < 8:
            return "High risk of harm from unprotected sun exposure"
        elif uvi < 11:
            return "Very high risk of harm from unprotected sun exposure"
        else:
            return "Extreme risk of harm from unprotected sun exposure"
    
    def _get_uv_protection_advice(self, uvi: Optional[float]) -> str:
        """Get UV protection advice based on UV index value.
        
        Args:
            uvi: UV index value
            
        Returns:
            Protection advice
        """
        if uvi is None:
            return "Use sun protection as a precaution"
            
        if uvi < 3:
            return "Wear sunglasses on bright days; use sunscreen if outside for more than an hour."
        elif uvi < 6:
            return "Wear sunglasses and use SPF 30+ sunscreen, cover the body with clothing and a hat, seek shade around midday."
        elif uvi < 8:
            return "Wear sunglasses and use SPF 30+ sunscreen, cover the body with sun protective clothing and a wide-brim hat, reduce time in the sun within three hours of solar noon."
        elif uvi < 11:
            return "Wear SPF 30+ sunscreen, a shirt, sunglasses, and a hat. Do not stay in the sun for too long."
        else:
            return "Take all precautions: Wear sunglasses and use SPF 30+ sunscreen, cover the body with a long-sleeve shirt and trousers, wear a very broad hat, avoid the sun from three hours before until three hours after solar noon."
    
    def _get_visibility_description(self, visibility_km: float) -> str:
        """Get visibility description based on kilometers.
        
        Args:
            visibility_km: Visibility in kilometers
            
        Returns:
            Visibility description
        """
        if visibility_km < 0.05:
            return "Dense fog"
        elif visibility_km < 0.2:
            return "Thick fog"
        elif visibility_km < 0.5:
            return "Moderate fog"
        elif visibility_km < 1:
            return "Light fog"
        elif visibility_km < 2:
            return "Thin fog / Mist"
        elif visibility_km < 4:
            return "Haze"
        elif visibility_km < 10:
            return "Light haze / Clear"
        else:
            return "Very clear"
    
    def _get_pressure_description(self, pressure: float) -> str:
        """Get pressure description based on hPa value.
        
        Args:
            pressure: Pressure in hPa
            
        Returns:
            Pressure description
        """
        if pressure < 970:
            return "Very low (storm conditions)"
        elif pressure < 990:
            return "Low (rainy or unsettled conditions)"
        elif pressure < 1010:
            return "Slightly low (changing conditions)"
        elif pressure < 1030:
            return "Normal / Average"
        elif pressure < 1050:
            return "High (fair weather)"
        else:
            return "Very high (very dry conditions)"
    
    def _get_humidity_comfort(self, humidity: float) -> str:
        """Get humidity comfort level description.
        
        Args:
            humidity: Relative humidity percentage
            
        Returns:
            Comfort level description
        """
        if humidity < 30:
            return "Very dry - may cause skin irritation and respiratory issues"
        elif humidity < 40:
            return "Dry - may cause mild discomfort for some"
        elif humidity < 60:
            return "Comfortable"
        elif humidity < 70:
            return "Slightly humid - may feel sticky"
        elif humidity < 80:
            return "Humid - uncomfortable for most people"
        else:
            return "Very humid - extremely uncomfortable"
    
    def _get_dew_point_description(self, dew_point: float) -> str:
        """Get dew point comfort description.
        
        Args:
            dew_point: Dew point in °C
            
        Returns:
            Comfort description
        """
        if dew_point < 10:
            return "Very comfortable - dry air"
        elif dew_point < 13:
            return "Comfortable - dry air"
        elif dew_point < 16:
            return "Comfortable - slight humidity"
        elif dew_point < 18:
            return "Moderately comfortable - noticeable humidity"
        elif dew_point < 21:
            return "Somewhat uncomfortable - humid and noticeable"
        elif dew_point < 24:
            return "Uncomfortable - very humid"
        else:
            return "Extremely uncomfortable - oppressive humidity"
    
    def get_outdoor_activity_recommendation(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a recommendation for outdoor activities based on weather.
        
        Args:
            weather_data: Weather data from the current() method.
            
        Returns:
            Recommendation as a structured JSON response.
        """
        response_time = self._get_current_date()
        
        # Extract current weather data
        current = weather_data.get("data", {}) if "data" in weather_data else weather_data.get("current", {})
        condition_code = current.get("condition", {}).get("code")
        temp_c = current.get("temp_c")
        is_day = current.get("is_day")
        humidity = current.get("humidity")
        wind_kph = current.get("wind_kph")
        
        recommendation = ""
        suitable_activities = []
        
        # Basic recommendations based on conditions
        if not is_day:
            recommendation = "It's nighttime, outdoor activities not recommended unless properly equipped."
            suitable_activities = ["night hiking", "stargazing", "night photography"]
        else:
            # Define severe and moderate weather condition codes for OpenWeatherMap
            # Severe weather conditions (thunderstorms, heavy snow, extreme rain, etc.)
            severe_conditions = [
                202, 212, 221, 232,  # Heavy thunderstorms
                302, 312, 314,       # Heavy drizzle
                502, 503, 504, 522,  # Heavy rain
                602, 622,            # Heavy snow
                751, 761, 762,       # Sand, dust, volcanic ash
                771, 781             # Squalls, tornado
            ]
            
            # Moderate weather conditions (light rain, light snow, fog, etc.)
            moderate_conditions = [
                200, 201, 210, 211, 230, 231,  # Light/moderate thunderstorms
                300, 301, 310, 311, 313, 321,  # Light/moderate drizzle
                500, 501, 520, 521, 531,       # Light/moderate rain
                600, 601, 611, 612, 613, 615, 616, 620, 621,  # Light/moderate snow
                701, 711, 721, 731, 741        # Mist, smoke, haze, fog
            ]
            
            # Use proper if-elif-else chain
            if condition_code in severe_conditions:
                recommendation = "Severe weather conditions. Outdoor activities not recommended."
                suitable_activities = ["indoor activities", "home workouts", "reading", "movies"]
            elif condition_code in moderate_conditions:
                recommendation = "Moderate weather conditions. Outdoor activities possible with proper equipment."
                suitable_activities = ["hiking", "jogging", "cycling", "walking"]
            elif temp_c < 0:
                recommendation = "Very cold temperatures. Bundle up for outdoor activities."
                suitable_activities = ["skiing", "snowboarding", "ice skating", "snowshoeing"]
            elif temp_c < 10:
                recommendation = "Cold temperatures. Dress warmly for outdoor activities."
                suitable_activities = ["hiking", "jogging", "brisk walking", "cycling"]
            elif temp_c > 30:
                recommendation = "Hot temperatures. Stay hydrated and avoid strenuous activities in the sun."
                suitable_activities = ["swimming", "water sports", "early morning activities", "evening activities"]
            elif wind_kph > 40:
                recommendation = "Strong winds. Be cautious with outdoor activities."
                suitable_activities = ["walking", "running", "activities in sheltered areas"]
            else:
                recommendation = "Good weather conditions for outdoor activities."
                suitable_activities = ["all outdoor activities", "picnics", "hiking", "sports", "gardening"]
        
        # Create structured response
        result = {
            "timestamp": response_time,
            "type": "outdoor_recommendation",
            "recommendation": recommendation,
            "suitable_activities": suitable_activities,
            "weather_snapshot": {
                "condition": current.get("condition", {}).get("text"),
                "temperature_c": temp_c,
                "is_day": is_day,
                "humidity": humidity,
                "wind_kph": wind_kph
            }
        }
        
        return result
    
    def get_complete_weather_data(self, location: str) -> Dict[str, Any]:
        """Get a comprehensive weather report including current conditions, forecasts, and moon phase.
        
        This combines multiple API calls into a single structured response.
        
        Args:
            location: Location name or coordinates.
            
        Returns:
            Dictionary with comprehensive weather information.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        
        try:
            # Get all the weather data
            current_weather = self.current(location)
            forecast_24h = self.get_forecast_24h(location)
            forecast_7day = self.get_forecast_7day(location)
            moon_phases = self.get_moon_phases(location, days=7)
            air_quality = self.get_air_quality(location)
            astronomy = self.get_astronomy(location)
            detailed_weather = self.get_detailed_weather(location)
            
            # Create structured complete response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "complete_weather_report",
                "is_cached": False,
                "location": current_weather.get("location", {}),
                "data": {
                    "current": current_weather.get("data", {}),
                    "air_quality": air_quality.get("data", {}),
                    "detailed": detailed_weather.get("data", {}),
                    "astronomy": astronomy.get("data", {}),
                    "forecast_24h": forecast_24h.get("data", {}),
                    "forecast_7day": forecast_7day.get("data", {}),
                    "moon_phases": moon_phases.get("data", {}).get("phases", [])[0:7],
                    "recommendation": self.get_outdoor_activity_recommendation(current_weather)
                }
            }
            
            return result
            
        except (NetworkError, APIError, MissingAPIKeyError) as e:
            # Handle errors but still try to return partial data
            partial_data = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "partial_weather_report",
                "error": str(e),
                "location": {"name": location},
                "data": {}
            }
            
            # Try to include whatever data we have
            try:
                partial_data["data"]["current"] = self.current(location).get("data", {})
            except Exception:
                pass
            
            try:
                partial_data["data"]["forecast_24h"] = self.get_forecast_24h(location).get("data", {})
            except Exception:
                pass
            
            try:
                partial_data["data"]["forecast_7day"] = self.get_forecast_7day(location).get("data", {})
            except Exception:
                pass
            
            try:
                partial_data["data"]["moon_phases"] = self.get_moon_phases(location, days=7).get("data", {}).get("phases", [])[0:7]
            except Exception:
                pass
            
            try:
                partial_data["data"]["air_quality"] = self.get_air_quality(location).get("data", {})
            except Exception:
                pass
            
            try:
                partial_data["data"]["astronomy"] = self.get_astronomy(location).get("data", {})
            except Exception:
                pass
            
            try:
                partial_data["data"]["detailed"] = self.get_detailed_weather(location).get("data", {})
            except Exception:
                pass
            
            # If we have any data, return it
            if partial_data["data"]:
                return partial_data
            
            # Otherwise re-raise the original error
            raise