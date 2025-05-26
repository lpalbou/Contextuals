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
        
        # Add system information - always available locally
        try:
            result["system"] = self.system.get_system_info()
        except Exception as e:
            result["system"] = {
                "timestamp": response_time,
                "type": "system_error",
                "error": str(e),
                "data": {"status": "unavailable"}
            }
        
        # Add user information - always available locally
        try:
            result["user"] = self.system.get_user_info()
        except Exception as e:
            result["user"] = {
                "timestamp": response_time,
                "type": "user_error", 
                "error": str(e),
                "data": {"status": "unavailable"}
            }
        
        # Add machine information - always available locally
        try:
            result["machine"] = self.system.get_machine_info()
        except Exception as e:
            result["machine"] = {
                "timestamp": response_time,
                "type": "machine_error",
                "error": str(e),
                "data": {"status": "unavailable"}
            }
        
        return result
    
    def get_simple_context(self) -> Dict[str, Any]:
        """Get simple contextual information suitable for LLM system prompts.
        
        Returns:
            Dictionary with simple contextual information.
        """
        # Get all context first
        all_context = self.get_all_context()
        
        # Extract simple information
        simple = {}
        
        # Time - extract ISO datetime
        if "time" in all_context and "data" in all_context["time"]:
            time_data = all_context["time"]["data"]
            simple["time"] = time_data.get("iso") or time_data.get("datetime") or all_context["time"]["timestamp"]
        else:
            simple["time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # User information
        if "user" in all_context and "data" in all_context["user"]:
            user_data = all_context["user"]["data"]
            simple["username"] = user_data.get("username", "unknown")
            simple["language"] = user_data.get("language", "unknown")
            simple["full_name"] = user_data.get("full_name", "")
        else:
            simple["username"] = "unknown"
            simple["language"] = "unknown"
            simple["full_name"] = ""
        
        # Location information
        simple["location"] = {
            "latitude": 0.0,
            "longitude": 0.0,
            "country": "unknown",
            "city": "unknown",
            "zip": "unknown"
        }
        
        if "location" in all_context and "data" in all_context["location"]:
            loc_data = all_context["location"]["data"]
            
            # Handle coordinates - check both possible structures
            if "coordinates" in loc_data:
                coords = loc_data["coordinates"]
                if "latitude" in coords and "longitude" in coords:
                    simple["location"]["latitude"] = float(coords["latitude"])
                    simple["location"]["longitude"] = float(coords["longitude"])
            elif "lat" in loc_data and "lon" in loc_data:
                simple["location"]["latitude"] = float(loc_data["lat"])
                simple["location"]["longitude"] = float(loc_data["lon"])
            
            if "country" in loc_data:
                simple["location"]["country"] = loc_data["country"]
            elif "address" in loc_data and "country" in loc_data["address"]:
                simple["location"]["country"] = loc_data["address"]["country"]
            
            if "name" in loc_data:
                # Try to extract city from name
                simple["location"]["city"] = loc_data["name"].split(",")[0].strip()
            elif "address" in loc_data and "city" in loc_data["address"]:
                simple["location"]["city"] = loc_data["address"]["city"]
            
            # Handle zip code - check both possible field names
            if "address" in loc_data:
                address = loc_data["address"]
                if "zip" in address:
                    simple["location"]["zip"] = address["zip"]
                elif "postcode" in address:
                    simple["location"]["zip"] = address["postcode"]
        
        # Weather information
        simple["weather"] = {
            "temp_c": 0.0,
            "sky": "unknown",
            "cloud": 0,
            "wind_kph": 0.0,
            "wind_dir": "unknown",
            "humidity": 0,
            "visibility": 0
        }
        
        if "weather" in all_context and "data" in all_context["weather"]:
            weather_data = all_context["weather"]["data"]
            simple["weather"]["temp_c"] = weather_data.get("temp_c", 0.0)
            simple["weather"]["cloud"] = weather_data.get("cloud", 0)
            simple["weather"]["wind_kph"] = weather_data.get("wind_kph", 0.0)
            simple["weather"]["wind_dir"] = weather_data.get("wind_dir", "unknown")
            simple["weather"]["humidity"] = weather_data.get("humidity", 0)
            simple["weather"]["visibility"] = weather_data.get("visibility", 0)
            
            # Extract sky condition
            if "condition" in weather_data and "text" in weather_data["condition"]:
                simple["weather"]["sky"] = weather_data["condition"]["text"]
            else:
                simple["weather"]["sky"] = "unknown"
        
        # Air quality information
        simple["air_quality"] = {
            "pollutants": {
                "co": 0.0,
                "o3": 0.0,
                "no2": 0.0,
                "so2": 0.0,
                "pm2_5": 0.0,
                "pm10": 0.0,
                "nh3": 0.0
            },
            "aqi": {
                "value": 1,
                "description": "No data",
                "health_implications": "No data available"
            },
            "recommendations": {
                "general": "No data",
                "sensitive_groups": "No data",
                "outdoor_activity": "No data",
                "ventilation": "No data"
            }
        }
        
        if "air_quality" in all_context and "data" in all_context["air_quality"]:
            aq_data = all_context["air_quality"]["data"]
            
            # Extract pollutants
            if "pollutants" in aq_data:
                pollutants = aq_data["pollutants"]
                simple["air_quality"]["pollutants"]["co"] = pollutants.get("co", 0.0)
                simple["air_quality"]["pollutants"]["o3"] = pollutants.get("o3", 0.0)
                simple["air_quality"]["pollutants"]["no2"] = pollutants.get("no2", 0.0)
                simple["air_quality"]["pollutants"]["so2"] = pollutants.get("so2", 0.0)
                simple["air_quality"]["pollutants"]["pm2_5"] = pollutants.get("pm2_5", 0.0)
                simple["air_quality"]["pollutants"]["pm10"] = pollutants.get("pm10", 0.0)
                simple["air_quality"]["pollutants"]["nh3"] = pollutants.get("nh3", 0.0)
            
            # Extract AQI
            if "aqi" in aq_data:
                aqi = aq_data["aqi"]
                simple["air_quality"]["aqi"]["value"] = aqi.get("value", 1)
                simple["air_quality"]["aqi"]["description"] = aqi.get("description", "No data")
                simple["air_quality"]["aqi"]["health_implications"] = aqi.get("health_implications", "No data available")
            
            # Extract recommendations
            if "recommendations" in aq_data:
                recs = aq_data["recommendations"]
                simple["air_quality"]["recommendations"]["general"] = recs.get("general", "No data")
                simple["air_quality"]["recommendations"]["sensitive_groups"] = recs.get("sensitive_groups", "No data")
                simple["air_quality"]["recommendations"]["outdoor_activity"] = recs.get("outdoor_activity", "No data")
                simple["air_quality"]["recommendations"]["ventilation"] = recs.get("ventilation", "No data")
        
        # Astronomy information
        simple["astronomy"] = {
            "sunrise": "unknown",
            "sunset": "unknown",
            "phase_description": "unknown"
        }
        
        if "astronomy" in all_context and "data" in all_context["astronomy"]:
            astro_data = all_context["astronomy"]["data"]
            
            if "sun" in astro_data:
                sun_data = astro_data["sun"]
                simple["astronomy"]["sunrise"] = sun_data.get("sunrise", "unknown")
                simple["astronomy"]["sunset"] = sun_data.get("sunset", "unknown")
            
            if "moon" in astro_data:
                moon_data = astro_data["moon"]
                simple["astronomy"]["phase_description"] = moon_data.get("phase_description", "unknown")
        
        # News information (simplified to empty list)
        simple["news"] = []
        if "news" in all_context and "data" in all_context["news"] and "articles" in all_context["news"]["data"]:
            # Keep only essential info for top 3 articles
            articles = all_context["news"]["data"]["articles"][:3]
            for article in articles:
                simple["news"].append({
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("name", "")
                })
        
        # Machine information
        simple["machine"] = {
            "platform": "unknown",
            "model": "unknown",
            "memory_total": 0.0,
            "memory_free": 0.0,
            "disk_total": 0.0,
            "disk_free": 0.0
        }
        
        if "machine" in all_context and "data" in all_context["machine"]:
            machine_data = all_context["machine"]["data"]
            simple["machine"]["platform"] = machine_data.get("platform", "unknown")
            
            # Extract CPU model
            if "cpu" in machine_data and "model" in machine_data["cpu"]:
                simple["machine"]["model"] = machine_data["cpu"]["model"]
            else:
                simple["machine"]["model"] = machine_data.get("processor", "unknown")
            
            # Extract memory info
            if "memory" in machine_data:
                memory = machine_data["memory"]
                simple["machine"]["memory_total"] = memory.get("total_mb", 0.0) / 1024.0  # Convert to GB
                simple["machine"]["memory_free"] = memory.get("free_mb", 0.0) / 1024.0   # Convert to GB
            
            # Extract disk info
            if "disk" in machine_data:
                disk = machine_data["disk"]
                simple["machine"]["disk_total"] = disk.get("total_gb", 0.0)
                simple["machine"]["disk_free"] = disk.get("free_gb", 0.0)
        
        return simple
    
    def get_simple_context_markdown(self) -> str:
        """Get simple contextual information formatted as Markdown.
        
        Returns:
            Markdown-formatted string with simple contextual information.
        """
        simple = self.get_simple_context()
        
        md_lines = []
        md_lines.append("# Contextual Information")
        md_lines.append("")
        
        # Time
        md_lines.append(f"**Time:** {simple['time']}")
        md_lines.append("")
        
        # User
        md_lines.append("## User Information")
        md_lines.append(f"- **Username:** {simple['username']}")
        md_lines.append(f"- **Full Name:** {simple['full_name']}")
        md_lines.append(f"- **Language:** {simple['language']}")
        md_lines.append("")
        
        # Location
        md_lines.append("## Location")
        loc = simple['location']
        md_lines.append(f"- **City:** {loc['city']}")
        md_lines.append(f"- **Country:** {loc['country']}")
        md_lines.append(f"- **Coordinates:** {loc['latitude']:.4f}, {loc['longitude']:.4f}")
        md_lines.append(f"- **Zip Code:** {loc['zip']}")
        md_lines.append("")
        
        # Weather
        md_lines.append("## Weather")
        weather = simple['weather']
        md_lines.append(f"- **Temperature:** {weather['temp_c']}°C")
        md_lines.append(f"- **Sky:** {weather['sky']}")
        md_lines.append(f"- **Cloud Cover:** {weather['cloud']}%")
        md_lines.append(f"- **Wind:** {weather['wind_kph']} km/h {weather['wind_dir']}")
        md_lines.append(f"- **Humidity:** {weather['humidity']}%")
        md_lines.append(f"- **Visibility:** {weather['visibility']} meters")
        md_lines.append("")
        
        # Air Quality
        md_lines.append("## Air Quality")
        aq = simple['air_quality']
        md_lines.append(f"- **AQI:** {aq['aqi']['value']} ({aq['aqi']['description']})")
        md_lines.append(f"- **Health Implications:** {aq['aqi']['health_implications']}")
        md_lines.append(f"- **General Recommendation:** {aq['recommendations']['general']}")
        md_lines.append("")
        
        # Astronomy
        md_lines.append("## Astronomy")
        astro = simple['astronomy']
        md_lines.append(f"- **Sunrise:** {astro['sunrise']}")
        md_lines.append(f"- **Sunset:** {astro['sunset']}")
        md_lines.append(f"- **Moon Phase:** {astro['phase_description']}")
        md_lines.append("")
        
        # News
        if simple['news']:
            md_lines.append("## Recent News")
            for i, article in enumerate(simple['news'], 1):
                md_lines.append(f"{i}. **{article['title']}** _{article['source']}_")
            md_lines.append("")
        
        # Machine
        md_lines.append("## Machine Information")
        machine = simple['machine']
        md_lines.append(f"- **Platform:** {machine['platform']}")
        md_lines.append(f"- **Model:** {machine['model']}")
        md_lines.append(f"- **Memory:** {machine['memory_free']:.1f}GB free / {machine['memory_total']:.1f}GB total")
        md_lines.append(f"- **Disk:** {machine['disk_free']:.1f}GB free / {machine['disk_total']:.1f}GB total")
        
        return "\n".join(md_lines)
    
    def get_all_context_json(self, minified: bool = False) -> str:
        """Get all contextual information as JSON string.
        
        Args:
            minified: If True, return minified JSON without indentation.
            
        Returns:
            JSON string with all contextual information.
        """
        import json
        data = self.get_all_context()
        if minified:
            return json.dumps(data, separators=(',', ':'))
        else:
            return json.dumps(data, indent=2)
    
    def get_simple_context_json(self, minified: bool = False) -> str:
        """Get simple contextual information as JSON string.
        
        Args:
            minified: If True, return minified JSON without indentation.
            
        Returns:
            JSON string with simple contextual information.
        """
        import json
        data = self.get_simple_context()
        if minified:
            return json.dumps(data, separators=(',', ':'))
        else:
            return json.dumps(data, indent=2)
