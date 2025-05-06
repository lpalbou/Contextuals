"""Advanced usage examples for Contextual-CC."""

import os
import time
from contextual_cc import ContextualCC
from contextual_cc.core.exceptions import (
    APIError, NetworkError, MissingAPIKeyError, FallbackError
)

def custom_configuration():
    """Demonstrate custom configuration."""
    print("===== CUSTOM CONFIGURATION =====")
    
    # Initialize with custom configuration
    context = ContextualCC(
        # Cache settings
        cache_duration=600,  # 10 minutes
        
        # Fallback settings
        use_fallback=True,
        
        # Time sync settings
        time_auto_sync=True,
        time_sync_interval=300,  # 5 minutes
    )
    
    # Get current time to see the configuration in action
    now = context.time.now()
    print(f"Current time with custom configuration: {now.isoformat()}")
    
    # Update configuration after initialization
    context.update_config(cache_duration=1800)  # 30 minutes
    print("Updated cache duration to 30 minutes")
    
    return context

def api_key_management():
    """Demonstrate API key management."""
    print("\n===== API KEY MANAGEMENT =====")
    
    # Method 1: Environment variables (set before running this script)
    # export CONTEXTUAL_CC_WEATHER_API_KEY="your_api_key"
    env_key = os.environ.get("CONTEXTUAL_CC_WEATHER_API_KEY")
    print(f"Weather API key from environment: {'Set' if env_key else 'Not set'}")
    
    # Method 2: Constructor parameters
    context = ContextualCC(
        weather_api_key="constructor_example_key"
    )
    print("Set weather API key via constructor")
    
    # Method 3: Set after initialization
    context.set_api_key("weather", "set_after_init_example_key")
    print("Set weather API key after initialization")
    
    return context

def error_handling():
    """Demonstrate error handling."""
    print("\n===== ERROR HANDLING =====")
    
    # Initialize without API keys to demonstrate error handling
    context = ContextualCC(use_fallback=False)  # Disable fallbacks to force errors
    
    # Try to get weather information without an API key
    try:
        weather = context.weather.current(location="Paris")
        print(f"Weather in Paris: {weather['current']['condition']['text']}")
    except MissingAPIKeyError as e:
        print(f"API key error: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")
    except APIError as e:
        print(f"API error: {e}")
    except FallbackError as e:
        print(f"Fallback error: {e}")
    except Exception as e:
        print(f"Other error: {e}")
    
    # Try with fallbacks enabled
    context = ContextualCC(use_fallback=True)
    print("\nWith fallbacks enabled:")
    
    try:
        # This might use cached data if available
        location = context.location.get("Mount Everest")
        print(f"Location resolved: {location['name']}")
    except Exception as e:
        print(f"Error even with fallbacks: {e}")
    
    return context

def caching_demonstration():
    """Demonstrate caching behavior."""
    print("\n===== CACHING DEMONSTRATION =====")
    
    context = ContextualCC(cache_duration=10)  # Short cache for demonstration
    
    # First request will go to the API
    print("Making first request...")
    try:
        start = time.time()
        location = context.location.get("Statue of Liberty")
        duration = time.time() - start
        print(f"First request took {duration:.2f} seconds")
        print(f"Location: {location['name']}")
    except Exception as e:
        print(f"First request failed: {e}")
        return None
    
    # Second request should be from cache (much faster)
    print("\nMaking second request (should use cache)...")
    try:
        start = time.time()
        location = context.location.get("Statue of Liberty")
        duration = time.time() - start
        print(f"Second request took {duration:.2f} seconds")
        print(f"Location: {location['name']}")
    except Exception as e:
        print(f"Second request failed: {e}")
    
    # Clear cache and try again
    print("\nClearing cache...")
    context.clear_cache()
    
    print("Making third request (after cache clear)...")
    try:
        start = time.time()
        location = context.location.get("Statue of Liberty")
        duration = time.time() - start
        print(f"Third request took {duration:.2f} seconds")
        print(f"Location: {location['name']}")
    except Exception as e:
        print(f"Third request failed: {e}")
    
    return context

def advanced_time_features():
    """Demonstrate advanced time features."""
    print("\n===== ADVANCED TIME FEATURES =====")
    
    context = ContextualCC()
    
    # Force sync with time API
    success = context.time.force_sync()
    print(f"Time sync successful: {success}")
    
    # Get the offset between local and server time
    offset = context.time.get_offset()
    print(f"Time offset from server: {offset:.2f} seconds")
    
    # Get timezone information
    try:
        tz_info = context.time.get_timezone_info("Europe/Paris")
        print("Paris timezone:")
        print(f"  Offset from UTC: {tz_info['offset']} hours")
        print(f"  DST in effect: {tz_info['dst']}")
        print(f"  Current time: {tz_info['current_time']}")
    except Exception as e:
        print(f"Could not get timezone info: {e}")
    
    # Use utility functions
    from contextual_cc.time.utils import get_day_period, format_duration
    
    now = context.time.now()
    period = get_day_period(now)
    print(f"Current period of the day: {period}")
    
    duration = format_duration(3661)  # 1 hour, 1 minute, 1 second
    print(f"Formatted duration: {duration}")
    
    return context

def advanced_weather_features():
    """Demonstrate advanced weather features."""
    print("\n===== ADVANCED WEATHER FEATURES =====")
    
    # Check if we have a weather API key
    api_key = os.environ.get("CONTEXTUAL_CC_WEATHER_API_KEY")
    if not api_key:
        print("Weather API key not set. Skipping advanced weather examples.")
        return None
    
    context = ContextualCC()
    
    try:
        # Get a weather forecast
        forecast = context.weather.get_forecast(location="Sydney", days=3)
        print(f"Weather forecast for {forecast['location']['name']}:")
        
        for day in forecast["forecast"]:
            print(f"Date: {day['date']}")
            print(f"  Condition: {day['condition']}")
            print(f"  Temperature range: {day['min_temp_c']}°C to {day['max_temp_c']}°C")
        
        # Get air quality
        try:
            air_quality = context.weather.get_air_quality(location="Sydney")
            print("\nSydney air quality:")
            print(f"  PM2.5: {air_quality['pm2_5']}")
            print(f"  PM10: {air_quality['pm10']}")
            print(f"  EPA Index: {air_quality['us-epa-index']}")
        except Exception as e:
            print(f"Could not get air quality: {e}")
        
        # Weather condition interpretation
        current = context.weather.current(location="Sydney")
        condition_code = current['current']['condition']['code']
        description = context.weather.interpret_condition(condition_code)
        print(f"\nWeather condition interpretation: {description}")
        
        # Use utility functions
        from contextual_cc.weather.utils import (
            get_comfort_level, calculate_heat_index, get_uv_index_description
        )
        
        temp = current['current']['temp_c']
        humidity = current['current']['humidity']
        
        comfort = get_comfort_level(temp, humidity)
        print(f"Comfort level: {comfort}")
        
        heat_index = calculate_heat_index(temp, humidity)
        print(f"Heat index: {heat_index:.1f}°C")
        
        uv = current['current']['uv']
        uv_desc = get_uv_index_description(uv)
        print(f"UV index: {uv} ({uv_desc})")
        
    except Exception as e:
        print(f"Weather operations failed: {e}")
    
    return context

def advanced_location_features():
    """Demonstrate advanced location features."""
    print("\n===== ADVANCED LOCATION FEATURES =====")
    
    context = ContextualCC()
    
    try:
        # Get timezone for coordinates
        timezone = context.location.get_timezone(latitude=35.6762, longitude=139.6503)
        print(f"Tokyo timezone: {timezone['timezone']}")
        
        # Find nearby locations
        nearby = context.location.get_nearby_locations(
            latitude=48.8584, longitude=2.2945,  # Eiffel Tower
            radius=2.0,  # 2 km radius
            limit=5
        )
        
        print(f"\nFound {len(nearby)} locations near the Eiffel Tower:")
        for place in nearby:
            print(f"- {place['name']} ({place['distance']:.2f} km)")
        
        # Use utility functions
        from contextual_cc.location.utils import (
            parse_coordinates, format_coordinates, get_cardinal_direction
        )
        
        # Parse coordinates in different formats
        coords = parse_coordinates("48.8584, 2.2945")
        print(f"\nParsed coordinates: {coords}")
        
        # Format coordinates in different formats
        dms = format_coordinates(48.8584, 2.2945, format_type="dms")
        print(f"Coordinates in DMS format: {dms}")
        
        # Calculate cardinal direction
        direction = get_cardinal_direction(
            lat1=48.8584, lon1=2.2945,  # Eiffel Tower
            lat2=48.8606, lon2=2.3376   # Louvre Museum
        )
        print(f"Direction from Eiffel Tower to Louvre: {direction}")
        
    except Exception as e:
        print(f"Advanced location operations failed: {e}")
    
    return context

def main():
    """Run all advanced examples."""
    # Run each demonstration
    custom_configuration()
    api_key_management()
    error_handling()
    caching_demonstration()
    advanced_time_features()
    advanced_weather_features()
    advanced_location_features()
    
    print("\nAdvanced examples completed.")

if __name__ == "__main__":
    main()