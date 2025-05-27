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

### Basic Installation

```bash
# Basic installation (core functionality only)
pip install contextuals

# With CLI support
pip install "contextuals[cli]"

# With benchmarking capabilities  
pip install "contextuals[benchmarks]"

# Full installation (CLI + benchmarks)
pip install "contextuals[full]"
```

### Development Installation

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

### Installation Options

- **`contextuals`**: Core library with contextual information features (includes feedparser for news)
- **`contextuals[cli]`**: Adds command-line interface support (same as core - CLI is always included)
- **`contextuals[benchmarks]`**: Adds model benchmarking capabilities (requires pydantic-ai)
- **`contextuals[full]`**: Complete installation with all features

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

### API Keys

- **Weather**: Get from [OpenWeatherMap.org](https://openweathermap.org/api)
  - Free tier provides access to current weather, 5-day forecast, and air quality
  - For 7-day forecasts and moon phases with precise data, consider subscribing to the "One Call API 3.0"
- **News**: No API key required! Uses free RSS feeds from reputable sources (BBC, Reuters, Google News, AP)
  - Completely free forever with no rate limits
  - Supports country-specific news and category filtering
  - Backward compatible with NewsAPI format
  - Requires `feedparser` dependency (automatically installed)

### Setting API Keys

You can set API keys in three ways:

1. **Environment Variables**:
   ```bash
   export CONTEXTUALS_WEATHER_API_KEY="your_weather_api_key"
   # News API key is no longer needed - RSS feeds are used instead
   ```

2. **Constructor Parameters**:
   ```python
   context = Contextuals(
       weather_api_key="your_weather_api_key"
       # news_api_key no longer needed - RSS feeds are used instead
   )
   ```

3. **After Initialization**:
   ```python
   context = Contextuals()
   context.set_api_key("weather", "your_weather_api_key")
   # context.set_api_key("news", "your_news_api_key")  # No longer needed
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
```

### Basic Commands

```bash
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

# Get system information
contextuals system

# Get user information
contextuals user

# Get machine information  
contextuals machine
```

### News Commands

```bash
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
```

### Comprehensive Context Commands

```bash
# Get all available contextual information (includes system, user, machine data)
contextuals all

# Get all contextual information as JSON
contextuals all --format json

# Get minified JSON (reduces size by ~20-25%)
contextuals all --format json --minified

# Get simple contextual information optimized for LLM prompts
contextuals simple

# Get simple contextual information as markdown
contextuals simple --format markdown

# Get minified simple JSON for LLM prompts
contextuals simple --format json --minified
```

### AI-Optimized Prompt Commands

```bash
# Get optimized context prompt for LLM system messages (DEFAULT variant)
contextuals prompt

# Get different prompt variants
contextuals prompt --variant structured  # Best overall quality (8.21/10) - RECOMMENDED
contextuals prompt --variant default     # Best speed-quality balance (36.35 tok/s)
contextuals prompt --variant compact     # Most token-efficient (~28 tokens)
contextuals prompt --variant minimal     # Ultra-compact (~20 tokens)
contextuals prompt --variant detailed    # Comprehensive context (~219 tokens)
```

### Benchmarking Commands

```bash
# Install with benchmarking support
pip install "contextuals[benchmarks]"

# Run benchmark on specific models
python -m contextuals.benchmarks.cli gemma3:1b qwen3:30b-a3b-q4_K_M

# Analyze existing benchmark results
python -c "from contextuals.benchmarks import analyze_results; analyze_results()"
```

### Help and Information

```bash
# Get help for any command
contextuals --help
contextuals all --help
contextuals prompt --help
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

# Get comprehensive context for AI applications
all_context = context.get_all_context()
simple_context = context.get_simple_context()
ai_prompt = context.get_context_prompt_structured()  # Recommended variant
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

Contextuals provides optimized prompts specifically designed for LLM system messages:

```python
from contextuals import Contextuals

# Initialize context provider
context = Contextuals()

# Get optimized context prompt for LLM system messages
system_prompt = context.get_context_prompt()

# Use with any LLM
import openai
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "What should I wear outside today?"}
    ]
)

# Different prompt variants for different needs
compact_prompt = context.get_context_prompt_compact()      # Most token-efficient
minimal_prompt = context.get_context_prompt_minimal()      # Ultra-compact
structured_prompt = context.get_context_prompt_structured() # JSON-like format
detailed_prompt = context.get_context_prompt_detailed()    # Comprehensive context

# Programmatic access to simple context data
simple_data = context.get_simple_context()
simple_json = context.get_simple_context_json(minified=True)
simple_markdown = context.get_simple_context_markdown()
```

**Empirical Testing Results:**
Based on comprehensive testing across 8 language models with LLM-as-a-judge evaluation, the prompt variants ranked as follows:
1. **STRUCTURED** (7.18/10 score) - Best overall quality with JSON-like format
2. **DEFAULT** (6.56/10 score) - Good balance with natural language format  
3. **COMPACT** (5.52/10 score) - Token-efficient but slower than expected

**Recommendations Based on Empirical Testing:**

**🏆 Best Overall Quality:** Use `STRUCTURED` variant (7.18/10 average score)
```python
prompt = context.get_context_prompt_structured()
```

**🚀 Best Speed-Quality Balance:** Use `DEFAULT` variant (59.2 tokens/sec with qwen3:30b)
```python
prompt = context.get_context_prompt()  # DEFAULT variant
```

**💰 Most Token-Efficient:** Use `COMPACT` variant (~100 tokens, note: speed paradox)
```python
prompt = context.get_context_prompt_compact()
```

**🎯 Recommended Model Combinations (from benchmark testing):**
- **Premium Quality**: qwen3:30b-a3b-q4_K_M + STRUCTURED (thinking capabilities)
- **Production Balance**: gemma3:12b + STRUCTURED (good speed)
- **Speed Critical**: gemma3:1b + DEFAULT (118.8 tokens/sec)
- **Reliable Choice**: granite3.3:8b + STRUCTURED (solid performance)

**💻 Memory-Constrained Recommendations:**

**For systems with < 8GB RAM:**
- **Best Choice**: `gemma3:1b` + DEFAULT variant (118.8 tokens/sec, ~2-3GB RAM)
- **Alternative**: `gemma3:3b` + STRUCTURED variant (if available, ~4-5GB RAM)
- **Note**: These models are surprisingly effective despite their size and provide excellent speed

**For systems with < 16GB RAM:**
- **Recommended**: `granite3.3:8b` + STRUCTURED variant (~6-8GB RAM, solid performance)
- **Alternative**: `gemma3:12b` + STRUCTURED variant (~8-12GB RAM, good balance)
- **Avoid**: 30B+ models which typically require 20GB+ RAM even when quantized

**Memory Usage Guidelines:**
- **1B models**: ~2-4GB RAM (excellent for laptops and development)
- **3-8B models**: ~4-10GB RAM (good balance for most users)
- **12B models**: ~8-16GB RAM (high quality, needs decent hardware)
- **30B+ models**: ~20GB+ RAM (workstation/server class hardware required)

See [BENCHMARK.md](docs/BENCHMARK.md) for complete empirical testing results across 8 models.

### Benchmarking

The library includes a comprehensive benchmarking system to evaluate prompt effectiveness across different models:

```python
from contextuals import ModelBenchmark
import asyncio

# Run benchmark programmatically
async def run_benchmark():
    benchmark = ModelBenchmark()
    results, evaluations = await benchmark.run_benchmark(["gemma3:1b", "qwen3:30b-a3b-q4_K_M"])
    return results, evaluations

# Analyze results
from contextuals.benchmarks import analyze_results
analyze_results()  # Processes comprehensive_results.json

# Or use the CLI
# python -m contextuals.benchmarks.cli gemma3:1b qwen3:30b-a3b-q4_K_M
```

**Benchmark Features:**
- Tests DEFAULT, STRUCTURED, and COMPACT prompt variants
- Uses LLM-as-a-judge evaluation with multi-perspective scoring
- Measures contextual awareness, accuracy, and practical utility
- Detects thinking capabilities in models
- Saves detailed results for analysis
- Provides empirical recommendations for production use

**Key Findings from 8-Model Benchmark:**
- **STRUCTURED prompt variant wins** with 7.18/10 average score
- **qwen3:30b-a3b-q4_K_M** shows superior performance with thinking capabilities
- **Contextual prompts provide measurable benefits** across all model sizes
- **Token efficiency matters**: STRUCTURED offers best quality-efficiency balance
- **COMPACT variant shows speed paradox**: Slower than expected despite fewer tokens

See [BENCHMARK.md](docs/BENCHMARK.md) for comprehensive results and recommendations.

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