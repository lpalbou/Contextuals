"""Main entry point for Contextuals library."""

import datetime
from typing import Dict, Any, Optional, Union

from contextuals.core.config import Config
from contextuals.core.cache import Cache
from contextuals.core.context_manager import ContextManager
from contextuals.time.time_provider import TimeProvider


def _round_number(value: Union[int, float, None], precision: int = 3) -> Union[int, float, None]:
    """Round a number to specified precision.
    
    Args:
        value: Number to round
        precision: Number of decimal places
        
    Returns:
        Rounded number or None if input is None
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    return round(float(value), precision)


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
                # Context manager returns raw location data, so we need to wrap it
                result["location"] = {
                    "timestamp": response_time,
                    "request_time": response_time,
                    "type": "current_location",
                    "is_cached": True,
                    "data": current_location
                }
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
    
    def get_simple_context(self, include_news: int = 0) -> Dict[str, Any]:
        """Get simple contextual information suitable for LLM system prompts.
        
        Args:
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
        
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
                    simple["location"]["latitude"] = _round_number(coords["latitude"])
                    simple["location"]["longitude"] = _round_number(coords["longitude"])
            elif "lat" in loc_data and "lon" in loc_data:
                simple["location"]["latitude"] = _round_number(loc_data["lat"])
                simple["location"]["longitude"] = _round_number(loc_data["lon"])
            
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
            simple["weather"]["temp_c"] = _round_number(weather_data.get("temp_c", 0.0))
            simple["weather"]["cloud"] = weather_data.get("cloud", 0)  # Integer, no rounding needed
            simple["weather"]["wind_kph"] = _round_number(weather_data.get("wind_kph", 0.0))
            simple["weather"]["wind_dir"] = weather_data.get("wind_dir", "unknown")
            simple["weather"]["humidity"] = weather_data.get("humidity", 0)  # Integer, no rounding needed
            simple["weather"]["visibility"] = weather_data.get("visibility", 0)  # Integer, no rounding needed
            
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
                simple["air_quality"]["pollutants"]["co"] = _round_number(pollutants.get("co", 0.0))
                simple["air_quality"]["pollutants"]["o3"] = _round_number(pollutants.get("o3", 0.0))
                simple["air_quality"]["pollutants"]["no2"] = _round_number(pollutants.get("no2", 0.0))
                simple["air_quality"]["pollutants"]["so2"] = _round_number(pollutants.get("so2", 0.0))
                simple["air_quality"]["pollutants"]["pm2_5"] = _round_number(pollutants.get("pm2_5", 0.0))
                simple["air_quality"]["pollutants"]["pm10"] = _round_number(pollutants.get("pm10", 0.0))
                simple["air_quality"]["pollutants"]["nh3"] = _round_number(pollutants.get("nh3", 0.0))
            
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
        if include_news > 0 and "news" in all_context and "data" in all_context["news"] and "articles" in all_context["news"]["data"]:
            # Keep only essential info for requested number of articles
            articles = all_context["news"]["data"]["articles"][:include_news]
            for article in articles:
                simple["news"].append({
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", "")
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
                simple["machine"]["memory_total"] = _round_number(memory.get("total_mb", 0.0) / 1024.0)  # Convert to GB
                simple["machine"]["memory_free"] = _round_number(memory.get("free_mb", 0.0) / 1024.0)   # Convert to GB
                simple["machine"]["maxmem"] = simple["machine"]["memory_total"]  # Alias for maximum memory
            
            # Extract disk info
            if "disk" in machine_data:
                disk = machine_data["disk"]
                simple["machine"]["disk_total"] = _round_number(disk.get("total_gb", 0.0))
                simple["machine"]["disk_free"] = _round_number(disk.get("free_gb", 0.0))
        
        return simple
    
    def get_simple_context_markdown(self, include_news: int = 0) -> str:
        """Get simple contextual information formatted as Markdown.
        
        Args:
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
        
        Returns:
            Markdown-formatted string with simple contextual information.
        """
        simple = self.get_simple_context(include_news=include_news)
        
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
                md_lines.append(f"{i}. **{article['title']}** _{article['source']}_ - [{article['url']}]({article['url']})")
            md_lines.append("")
        
        # Machine
        md_lines.append("## Machine Information")
        machine = simple['machine']
        md_lines.append(f"- **Platform:** {machine['platform']}")
        md_lines.append(f"- **Model:** {machine['model']}")
        md_lines.append(f"- **Memory:** {machine['memory_free']:.1f}GB free / {machine['memory_total']:.1f}GB total")
        md_lines.append(f"- **Disk:** {machine['disk_free']:.1f}GB free / {machine['disk_total']:.1f}GB total")
        
        return "\n".join(md_lines)
    
    def get_context_prompt(self, include_news: int = 3) -> str:
        """Get contextual information formatted as an optimized LLM system prompt.
        
        Args:
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
        
        Returns:
            Optimized prompt string with contextual information for LLM usage.
        """
        simple_data = self.get_simple_context(include_news=include_news)
        
        # Create token-efficient prompt
        prompt_parts = []
        
        # Header - concise explanation
        prompt_parts.append("CONTEXT: Real-time user environment data for personalized responses.")
        
        # Core data in compact format
        prompt_parts.append(f"TIME: {simple_data['time']}")
        prompt_parts.append(f"USER: {simple_data['username']} ({simple_data['full_name']}) | Lang: {simple_data['language']}")
        
        # Location
        loc = simple_data['location']
        prompt_parts.append(f"LOCATION: {loc['city']}, {loc['country']} ({loc['latitude']:.2f},{loc['longitude']:.2f})")
        
        # Weather - most relevant info
        weather = simple_data['weather']
        prompt_parts.append(f"WEATHER: {weather['temp_c']}°C, {weather['sky']}, {weather['humidity']}% humidity, {weather['wind_kph']}km/h {weather['wind_dir']}")
        
        # Air quality - health relevant
        aq = simple_data['air_quality']
        prompt_parts.append(f"AIR: AQI {aq['aqi']['value']} ({aq['aqi']['description']}) - {aq['recommendations']['general']}")
        
        # Astronomy - time context
        astro = simple_data['astronomy']
        prompt_parts.append(f"SUN: Rise {astro['sunrise']}, Set {astro['sunset']} | Moon: {astro['phase_description']}")
        
        # Machine context - detailed memory and disk info
        machine = simple_data['machine']
        prompt_parts.append(f"SYSTEM: {machine['platform']}, {machine['model']}, memory: {machine['memory_free']:.0f}GB/{machine['maxmem']:.0f}GB, disk: {machine['disk_free']:.0f}GB/{machine['disk_total']:.0f}GB")
        
        # News if available and requested
        if simple_data['news']:
            news_items = []
            for article in simple_data['news']:
                title = article['title']
                url = article['url'][:30] + "..." if len(article['url']) > 30 else article['url']
                news_items.append(f"{title} ({url})")
            prompt_parts.append(f"NEWS: {' | '.join(news_items)}")
        
        # Context instructions - concise and natural
        usage_parts = ["Shared implicit context: current environment, location, time, weather, and system status."]
        usage_parts.append("Respond naturally with contextual awareness.")
        usage_parts.append("Consider system capabilities for technical suggestions.")
        
        # Add news guidance if news is present
        if simple_data['news']:
            usage_parts.append("Reference current events when relevant; provide URLs for follow-up when helpful.")
        
        prompt_parts.append(f"\nCONTEXT: {' '.join(usage_parts)}")
        
        return "\n".join(prompt_parts)
    
    def get_context_prompt_compact(self, include_news: int = 3) -> str:
        """Get ultra-compact contextual prompt for token efficiency.
        
        Args:
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
        """
        simple_data = self.get_simple_context(include_news=include_news)
        
        # Ultra-compact format with all essential information
        loc = simple_data['location']
        weather = simple_data['weather']
        astro = simple_data['astronomy']
        machine = simple_data['machine']
        
        compact_parts = [
            f"CTX: {simple_data['time'][:16]}",
            f"SR {astro['sunrise'][:5]}",
            f"SS {astro['sunset'][:5]}",
            f"USR: {simple_data['username']} ({simple_data['full_name'][:10]}...)",
            f"LANG: {simple_data['language'][:5]}",
            f"LOC: {loc['city']},{loc['country']} ({loc['latitude']:.2f},{loc['longitude']:.2f})",
            f"ENV: {weather['temp_c']}°C {weather['sky']} {weather['humidity']}% {weather['wind_kph']}km/h {weather['wind_dir']}",
            f"AQI:{simple_data['air_quality']['aqi']['value']} ({simple_data['air_quality']['aqi']['description'][:4]})",
            f"MOON: {simple_data['astronomy']['phase_description'][:8]}",
            f"SYS: {machine['platform']}",
            f"CPU: {machine['model'][:15]}",
            f"MEM {machine['memory_free']:.0f}GB/{machine['maxmem']:.0f}GB",
            f"DISK {machine['disk_free']:.0f}GB/{machine['disk_total']:.0f}GB"
        ]
        
        # Add news if requested (only compress titles, keep URLs full for COMPACT)
        if simple_data['news']:
            news_items = []
            for i, article in enumerate(simple_data['news'], 1):
                title = article['title'][:25] + "..." if len(article['title']) > 25 else article['title']
                url = article['url']  # Keep full URL - must remain usable
                news_items.append(f"NEWS{i} {title} ({url})")
            compact_parts.extend(news_items)
        
        # Context instructions for COMPACT
        usage_parts = ["Shared implicit context."]
        usage_parts.append("Respond with contextual awareness.")
        if simple_data['news']:
            usage_parts.append("Reference current events when relevant.")
        
        compact_parts.append(" ".join(usage_parts))
        
        return " | ".join(compact_parts)
    
    def get_context_prompt_detailed(self, include_news: int = 3) -> str:
        """Get detailed contextual prompt with comprehensive information.
        
        Args:
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
        """
        simple_data = self.get_simple_context(include_news=include_news)
        
        prompt_parts = []
        prompt_parts.append("=== CONTEXTUAL INFORMATION ===")
        prompt_parts.append("This data provides real-time user environment context for personalized assistance.")
        prompt_parts.append("")
        
        # Detailed sections
        prompt_parts.append(f"TEMPORAL CONTEXT:")
        prompt_parts.append(f"• Current time: {simple_data['time']}")
        prompt_parts.append("")
        
        prompt_parts.append(f"USER PROFILE:")
        prompt_parts.append(f"• Name: {simple_data['full_name']} ({simple_data['username']})")
        prompt_parts.append(f"• Language/Locale: {simple_data['language']}")
        prompt_parts.append("")
        
        loc = simple_data['location']
        prompt_parts.append(f"GEOGRAPHIC CONTEXT:")
        prompt_parts.append(f"• Location: {loc['city']}, {loc['country']}")
        prompt_parts.append(f"• Coordinates: {loc['latitude']:.4f}, {loc['longitude']:.4f}")
        prompt_parts.append("")
        
        weather = simple_data['weather']
        prompt_parts.append(f"ENVIRONMENTAL CONDITIONS:")
        prompt_parts.append(f"• Weather: {weather['temp_c']}°C, {weather['sky']}")
        prompt_parts.append(f"• Wind: {weather['wind_kph']} km/h {weather['wind_dir']}, Humidity: {weather['humidity']}%")
        
        aq = simple_data['air_quality']
        prompt_parts.append(f"• Air Quality: {aq['aqi']['description']} (AQI {aq['aqi']['value']})")
        prompt_parts.append(f"• Health Advice: {aq['recommendations']['general']}")
        prompt_parts.append("")
        
        astro = simple_data['astronomy']
        prompt_parts.append(f"ASTRONOMICAL DATA:")
        prompt_parts.append(f"• Sunrise: {astro['sunrise']}, Sunset: {astro['sunset']}")
        prompt_parts.append(f"• Moon Phase: {astro['phase_description']}")
        prompt_parts.append("")
        
        machine = simple_data['machine']
        prompt_parts.append(f"SYSTEM INFORMATION:")
        prompt_parts.append(f"• Platform: {machine['platform']}")
        prompt_parts.append(f"• Model: {machine['model']}")
        prompt_parts.append(f"• Memory: {machine['memory_free']:.0f}GB / {machine['memory_total']:.0f}GB")
        prompt_parts.append(f"• Disk: {machine['disk_free']:.0f}GB / {machine['disk_total']:.0f}GB")
        prompt_parts.append("")
        
        if simple_data['news']:
            prompt_parts.append(f"CURRENT NEWS CONTEXT:")
            for i, article in enumerate(simple_data['news'], 1):
                prompt_parts.append(f"• {article['title']} ({article['source']}) - {article['url']}")
            prompt_parts.append("")
        
        prompt_parts.append("CONTEXT AWARENESS:")
        prompt_parts.append("• Shared implicit context: location, time, weather, air quality, and system status")
        prompt_parts.append("• Respond naturally with contextual awareness")
        prompt_parts.append("• Provide contextually appropriate recommendations")
        prompt_parts.append("• Consider environmental factors for activity suggestions")
        prompt_parts.append("• Factor in system capabilities for technical recommendations")
        if simple_data['news']:
            prompt_parts.append("• Reference current events when relevant to the user's situation")
        
        return "\n".join(prompt_parts)
    
    def get_context_prompt_minimal(self, include_news: int = 3) -> str:
        """Get minimal contextual prompt for extreme token efficiency.
        
        Args:
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
        """
        simple_data = self.get_simple_context(include_news=include_news)
        
        loc = simple_data['location']
        weather = simple_data['weather']
        
        minimal_parts = [
            f"User: {simple_data['username']} in {loc['city']}, {loc['country']}",
            f"{weather['temp_c']}°C {weather['sky']}",
            f"{simple_data['time'][:16]}",
            f"Mem: {simple_data['machine']['memory_free']:.0f}GB/{simple_data['machine']['maxmem']:.0f}GB"
        ]
        
        # Add news if requested (very minimal for MINIMAL variant)
        if simple_data['news']:
            news_title = simple_data['news'][0]['title'][:15] + "..." if len(simple_data['news'][0]['title']) > 15 else simple_data['news'][0]['title']
            news_url = simple_data['news'][0]['url'][:10] + "..." if len(simple_data['news'][0]['url']) > 10 else simple_data['news'][0]['url']
            minimal_parts.append(f"News: {news_title} ({news_url})")
        
        # Context instructions for MINIMAL
        usage_parts = ["Shared context."]
        if simple_data['news']:
            usage_parts.append("Reference current events.")
        
        minimal_parts.append(" ".join(usage_parts))
        
        return " | ".join(minimal_parts)
    
    def get_context_prompt_structured(self, include_news: int = 3) -> str:
        """Get structured contextual prompt in JSON-like format.
        
        Args:
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
        """
        simple_data = self.get_simple_context(include_news=include_news)
        
        # Create structured format with all information
        import json
        
        context_data = {
            "user": f"{simple_data['username']} ({simple_data['full_name']})",
            "language": simple_data['language'],
            "location": f"{simple_data['location']['city']}, {simple_data['location']['country']}",
            "coordinates": f"{simple_data['location']['latitude']:.2f},{simple_data['location']['longitude']:.2f}",
            "time": simple_data['time'][:16],
            "temperature": f"{simple_data['weather']['temp_c']}°C",
            "humidity": f"{simple_data['weather']['humidity']}%",
            "wind": f"{simple_data['weather']['wind_kph']}km/h {simple_data['weather']['wind_dir'][:3]}",
            "sky": simple_data['weather']['sky'],
            "aqi": simple_data['air_quality']['aqi']['value'],
            "air_quality": simple_data['air_quality']['aqi']['description'],
            "air_recommendation": simple_data['air_quality']['recommendations']['general'],
            "sunrise": simple_data['astronomy']['sunrise'],
            "sunset": simple_data['astronomy']['sunset'],
            "moon": simple_data['astronomy']['phase_description'],
            "system": simple_data['machine']['platform'],
            "cpu": simple_data['machine']['model'],
            "freemem": f"{simple_data['machine']['memory_free']:.0f}GB",
            "maxmem": f"{simple_data['machine']['maxmem']:.0f}GB",
            "freespace": f"{simple_data['machine']['disk_free']:.0f}GB",
            "maxspace": f"{simple_data['machine']['disk_total']:.0f}GB"
        }
        
        # Add news if requested
        if simple_data['news']:
            context_data["news"] = [{"title": article['title'], "url": article['url']} for article in simple_data['news']]
        
        # Create minified JSON for the prompt
        context_json = json.dumps(context_data, separators=(',', ':'))
        
        structured_parts = []
        structured_parts.append(f"CONTEXT_DATA: {context_json}")
        structured_parts.append("")
        # Context instructions for STRUCTURED
        instructions = ["Shared implicit context: environment, location, time, weather, and system status."]
        instructions.append("Respond naturally with contextual awareness.")
        instructions.append("Consider system capabilities for technical suggestions.")
        if simple_data['news']:
            instructions.append("Reference current events when relevant to the user's situation.")
        
        structured_parts.append(f"CONTEXT: {' '.join(instructions)}")
        
        return "\n".join(structured_parts)
    
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
    
    def get_simple_context_json(self, minified: bool = False, include_news: int = 0) -> str:
        """Get simple contextual information as JSON string.
        
        Args:
            minified: If True, return minified JSON without indentation.
            include_news: Number of news articles to include (0 = no news, 3 = default, 5, 10, etc.).
            
        Returns:
            JSON string with simple contextual information.
        """
        import json
        data = self.get_simple_context(include_news=include_news)
        if minified:
            return json.dumps(data, separators=(',', ':'))
        else:
            return json.dumps(data, indent=2)
