"""Basic usage examples for Contextuals."""

from contextuals import Contextuals

def main():
    """Demonstrate basic usage of Contextuals."""
    # Initialize with default configuration
    context = Contextuals()
    
    print("===== TIME CONTEXT =====")
    # Get current time
    now_utc = context.time.now()
    print(f"Current time (UTC): {now_utc.isoformat()}")
    
    # Get current time in a specific timezone
    try:
        now_ny = context.time.now(timezone="America/New_York")
        print(f"Current time (New York): {now_ny.isoformat()}")
    except Exception as e:
        print(f"Could not get timezone-specific time: {e}")
    
    # Format time
    formatted = context.time.format_time(now_utc, fmt="%Y-%m-%d %H:%M:%S")
    print(f"Formatted time: {formatted}")
    
    print("\n===== LOCATION CONTEXT =====")
    # Get location information
    try:
        location = context.location.get("Eiffel Tower")
        print(f"Location: {location['name']}")
        print(f"Coordinates: {location['coordinates']['latitude']}, {location['coordinates']['longitude']}")
        
        # Reverse geocoding
        lat, lon = location['coordinates']['latitude'], location['coordinates']['longitude']
        reverse = context.location.reverse_geocode(latitude=lat, longitude=lon)
        print(f"Reverse geocoded: {reverse['name']}")
        
        # Calculate distance
        distance = context.location.calculate_distance(
            lat1=48.8584, lon1=2.2945,  # Eiffel Tower
            lat2=48.8606, lon2=2.3376,  # Louvre Museum
            unit="km"
        )
        print(f"Distance from Eiffel Tower to Louvre: {distance:.2f} km")
    
    except Exception as e:
        print(f"Could not perform location operations: {e}")
    
    print("\n===== WEATHER CONTEXT =====")
    # Weather operations require an API key
    # You can set it via environment variable CONTEXTUALS_WEATHER_API_KEY
    # or pass it when initializing Contextuals
    
    # Try to get weather information
    try:
        weather = context.weather.current(location="London")
        print(f"Weather in {weather['location']['name']}:")
        print(f"  Condition: {weather['current']['condition']['text']}")
        print(f"  Temperature: {weather['current']['temp_c']}°C")
        print(f"  Humidity: {weather['current']['humidity']}%")
        print(f"  Wind: {weather['current']['wind_kph']} kph, {weather['current']['wind_dir']}")
        
        # Get outdoor activity recommendation
        recommendation = context.weather.get_outdoor_activity_recommendation(weather)
        print(f"Outdoor activity recommendation: {recommendation}")
        
    except Exception as e:
        print(f"Could not get weather information (API key may be required): {e}")
    
    print("\nSee more examples in the documentation.")

if __name__ == "__main__":
    main()