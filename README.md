# Contextuals

Contextuals is a Python library designed to provide comprehensive contextual information for AI applications with graceful fallbacks and efficient caching. This library helps ground AI in spatial, temporal, environmental, social/relational, and cultural contexts, with structured, consistent data formats.

## Features

- **Time Context**: Accurate time information with API synchronization and local fallback
- **Weather Context**: Rich environmental data including:
  - Current conditions with temperature, humidity, wind, etc.
  - Detailed 24-hour forecasts with hourly predictions
  - 7-day forecasts with daily weather patterns
  - Astronomical data (sunrise/sunset, moon phases, day length)
  - Air quality information with health recommendations based on WHO guidelines
  - UV index with exposure risks and protection advice
  - Visibility, pressure, and other meteorological details
- **Location Context**: Geographic and spatial information with geocoding and reverse geocoding
- **News Context**: Country-specific and world news with search capabilities
- **Caching**: Efficient TTL-based caching to minimize API calls
- **API Key Management**: Flexible API key configuration through environment variables or code
- **Location Awareness**: Automatically use current location for country-specific information
- **JSON Responses**: All responses structured as consistent JSON with proper timestamps
- **Fallbacks**: Graceful fallbacks when internet connection is unavailable
- **CLI Interface**: Easy command-line access to all contextual information

## Installation

The recommended way to install the library is using pip:

```bash
pip install contextuals
```

For development purposes, you can install from the GitHub repository:

```bash
# Clone the repository
git clone https://github.com/lpalbou/contextuals.git
cd contextuals

# Install with Poetry (recommended)
poetry install

# Activate the virtual environment
poetry shell
```

## Quick Start

```python
from contextuals import Contextuals

# Initialize the library
context = Contextuals()

# Get current time (synced with a time API when possible)
current_time = context.time.now(format_as_json=True)
print(f"Current time: {current_time['data']['datetime']}")

# Set current location
context.set_current_location("New York")

# Get weather information (requires API key)
try:
    weather = context.weather.current("New York")
    print(f"Weather in New York: {weather['data']['condition']['text']}, {weather['data']['temp_c']}°C")
except Exception as e:
    print(f"Weather information not available: {e}")

# Get news for the current location's country (requires API key)
try:
    news = context.news.get_country_news(category="technology")
    for article in news["data"]["articles"][:3]:  # Show first 3 articles
        print(f"- {article['title']}")
except Exception as e:
    print(f"News not available: {e}")
```

## Setting Up API Keys

Contextuals uses multiple APIs under the hood. Some of them require API keys:

### Required API Keys

- **Weather**: Get from [OpenWeatherMap.org](https://openweathermap.org/api)
  - Free tier provides access to current weather, 5-day forecast, and air quality
  - For 7-day forecasts and moon phases with precise data, consider subscribing to the "One Call API 3.0"
- **News**: Get from [NewsAPI.org](https://newsapi.org/)

### Setting API Keys

You can set API keys in three ways:

1. **Environment Variables**:
   ```bash
   export CONTEXTUALS_WEATHER_API_KEY="your_weather_api_key"
   export CONTEXTUALS_NEWS_API_KEY="your_news_api_key"
   ```

2. **Constructor Parameters**:
   ```python
   context = Contextuals(
       weather_api_key="your_weather_api_key",
       news_api_key="your_news_api_key"
   )
   ```

3. **After Initialization**:
   ```python
   context = Contextuals()
   context.set_api_key("weather", "your_weather_api_key")
   context.set_api_key("news", "your_news_api_key")
   ```

## Advanced Usage

### Time Context

```python
# Get time with different formatting
dt = context.time.now()  # Returns a datetime object
dt_json = context.time.now(format_as_json=True)  # Returns JSON structure

# Get time in different timezones
ny_time = context.time.now(timezone="America/New_York")
tokyo_time = context.time.now(timezone="Asia/Tokyo")

# Get timezone information
tz_info = context.time.get_timezone_info("Europe/Paris")
```

### Weather Context

```python
# Get current weather conditions
weather = context.weather.current("London")
print(f"Temperature: {weather['data']['temp_c']}°C")
print(f"Condition: {weather['data']['condition']['text']}")

# Get detailed 24-hour forecast
forecast_24h = context.weather.get_forecast_24h("London")
for hour in forecast_24h["data"]["hours"]:
    print(f"{hour['time']}: {hour['temp_c']}°C, {hour['condition']['text']}")

# Get 7-day forecast
forecast_7day = context.weather.get_forecast_7day("London")
for day in forecast_7day["data"]["days"]:
    print(f"{day['date']}: {day['min_temp_c']}°C to {day['max_temp_c']}°C")

# Get air quality with health recommendations
air_quality = context.weather.get_air_quality("London")
print(f"Air Quality Index: {air_quality['data']['aqi']['description']}")
print(f"Recommendation: {air_quality['data']['recommendations']['general']}")

# Get astronomy data (sunrise, sunset, moon phases)
astronomy = context.weather.get_astronomy("London")
print(f"Sunrise: {astronomy['data']['sun']['sunrise']}")
print(f"Sunset: {astronomy['data']['sun']['sunset']}")
print(f"Day length: {astronomy['data']['sun']['day_length']}")
print(f"Moon phase: {astronomy['data']['moon']['phase_description']}")

# Get detailed weather data (UV, visibility, pressure)
detailed = context.weather.get_detailed_weather("London")
print(f"UV Index: {detailed['data']['uv_index']['category']} - {detailed['data']['uv_index']['risk_level']}")
print(f"Visibility: {detailed['data']['visibility']['description']}")
print(f"Pressure: {detailed['data']['pressure']['description']}")

# Get comprehensive weather data (combines all of the above)
complete = context.weather.get_complete_weather_data("London")

# Get outdoor activity recommendations
recommendation = context.weather.get_outdoor_activity_recommendation(weather)
print(f"Recommendation: {recommendation['recommendation']}")
print(f"Suitable activities: {', '.join(recommendation['suitable_activities'])}")
```

#### Sample Weather Data Structure

Here's an example of the structured data you'll receive:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "current_weather",
  "is_cached": false,
  "location": {
    "name": "London",
    "country": "GB",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "temp_c": 15.5,
    "temp_f": 59.9,
    "is_day": 1,
    "condition": {
      "text": "Partly cloudy",
      "code": 802
    },
    "wind_mph": 8.1,
    "wind_kph": 13.0,
    "wind_degree": 270,
    "wind_dir": "W",
    "humidity": 76,
    "cloud": 25,
    "feelslike_c": 14.2,
    "feelslike_f": 57.6,
    "pressure": 1012,
    "visibility": 10000
  }
}
```

### Location Context

```python
# Get location information
location = context.location.get("Eiffel Tower")

# Reverse geocoding (coordinates to address)
address = context.location.reverse_geocode(48.8584, 2.2945)

# Get timezone for coordinates
timezone = context.location.get_timezone(48.8584, 2.2945)

# Calculate distance between two points
distance = context.location.calculate_distance(
    40.7128, -74.0060,  # New York
    34.0522, -118.2437  # Los Angeles
)
```

### News Context

```python
# Get news for the current location's country
local_news = context.news.get_country_news()

# Get world news
world_news = context.news.get_world_news()

# Search for specific news
ai_news = context.news.search_news("artificial intelligence")

# Get news by category
tech_news = context.news.get_country_news(category="technology")
```

## CLI Interface

Contextuals comes with a convenient command-line interface to quickly access contextual information:

```bash
# Install with CLI support
pip install "contextuals[cli]"

# Get current time
contextuals time

# Get current time in Tokyo
contextuals time --timezone Asia/Tokyo

# Get current time in JSON format
contextuals time --format json

# Get weather for your current location (auto-detected)
contextuals weather

# Get weather for a specific location
contextuals weather London

# Get detailed weather (UV, visibility, pressure)
contextuals weather --detailed

# Get all weather data (current, air quality, astronomy, forecasts)
contextuals weather --all

# Get air quality for current location
contextuals air-quality

# Get air quality for Paris
contextuals air-quality Paris

# Get astronomy data (sunrise/sunset, moon phases)
contextuals astronomy

# Get your current location
contextuals location

# Get information about a specific location
contextuals location "Eiffel Tower"

# Get news for your current location (auto-detected)
contextuals news

# Get world news
contextuals news --world

# Get news for a specific country
contextuals news --country fr  # France
contextuals news --country us  # United States
contextuals news --country gb  # United Kingdom

# Get category-specific news
contextuals news --category technology
contextuals news --country de --category business  # German business news

# Get news about a specific topic
contextuals news --search "artificial intelligence"

# Show more articles in the results
contextuals news --show 10


# Get all available contextual information
contextuals all

# Get all contextual information as JSON
contextuals all --format json

# Get help
contextuals --help
```

## Integration with Other Applications

### Basic Integration

```python
from contextuals import Contextuals

# Initialize with your API keys
context = Contextuals(
    weather_api_key="your_openweathermap_api_key",
    news_api_key="your_newsapi_key"
)

# Get any contextual information you need
time_info = context.time.now(format_as_json=True)
weather_info = context.weather.current("London")
location_info = context.location.get("London")
news_info = context.news.get_country_news("gb")
```

### Web Application Integration

```python
# Flask example
from flask import Flask, jsonify
from contextuals import Contextuals

app = Flask(__name__)
context = Contextuals()

@app.route('/api/time')
def get_time():
    return jsonify(context.time.now(format_as_json=True))

@app.route('/api/weather/<location>')
def get_weather(location):
    return jsonify(context.weather.current(location))

@app.route('/api/news')
def get_news():
    return jsonify(context.news.get_top_headlines())
```

### AI Integration

```python
import openai
from contextuals import Contextuals

# Initialize context provider
context = Contextuals()

# Get enriched context
time_info = context.time.now(format_as_json=True)
weather_info = context.weather.current("London")
news_info = context.news.get_top_headlines(country="gb", page_size=3)

# Create context-aware prompt
prompt = f"""
Current time: {time_info['data']['datetime']}
Current weather in London: {weather_info['data']['temp_c']}°C, {weather_info['data']['condition']['text']}
Top headlines:
- {news_info['data']['articles'][0]['title']}
- {news_info['data']['articles'][1]['title']}
- {news_info['data']['articles'][2]['title']}

Given this context, please provide a personalized greeting and suggestion for the user's day.
"""

# Send to OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
)
```

## Error Handling and Fallbacks

Contextuals is designed with robust error handling and fallbacks:

```python
try:
    weather = context.weather.current("London")
except Exception as e:
    # Handle API errors, network issues, etc.
    print(f"Could not get weather data: {e}")
    # Use fallback data if needed
    weather = {
        "data": {
            "temp_c": None,
            "condition": {"text": "Unknown"}
        }
    }
```

## Documentation

For detailed documentation, see the [docs](docs/) directory.

### Example Code

Check out the [examples](docs/examples/) directory for detailed usage examples:

- [basic_usage.py](docs/examples/basic_usage.py) - Simple introduction to the library features
- [advanced_usage.py](docs/examples/advanced_usage.py) - Advanced configuration and error handling
- [ai_integration.py](docs/examples/ai_integration.py) - Integrating contextual information with AI models
- [system_info.py](docs/examples/system_info.py) - Working with system and hardware information

## License

MIT License

See [LICENSE](LICENSE) for the full license text.

## Acknowledgments

This project uses several open-source libraries and services. See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) for a detailed list of dependencies and their licenses.