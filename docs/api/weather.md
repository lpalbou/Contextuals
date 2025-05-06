# Weather API Reference

This document provides detailed API reference for the weather context module in Contextual-CC.

## Table of Contents
- [WeatherProvider](#weatherprovider)
- [Utility Functions](#utility-functions)

## WeatherProvider

The WeatherProvider class provides weather-related contextual information.

### Constructor

```python
WeatherProvider(config: Config, cache: Cache)
```

**Parameters:**
- `config`: Configuration instance
- `cache`: Cache instance

**Note:** You typically won't instantiate this class directly but access it through the `ContextualCC` interface.

### Methods

#### `current`

```python
current(location: str) -> Dict[str, Any]
```

Get current weather conditions for a location.

**Parameters:**
- `location`: Location name or coordinates

**Returns:**
- Dictionary with weather information:
  - `location`: Location information (name, region, country, etc.)
  - `current`: Current weather conditions (temperature, wind, etc.)
  - `is_cached`: Whether the data is from cache
  - `cached_at`: Timestamp when the data was cached

**Raises:**
- `NetworkError`: If API request fails and no fallback is available
- `APIError`: If API returns an error
- `MissingAPIKeyError`: If API key is not found

**Example:**
```python
from contextual_cc import ContextualCC

context = ContextualCC(weather_api_key="your_api_key")
weather = context.weather.current(location="London")

print(f"Weather in {weather['location']['name']}:")
print(f"Condition: {weather['current']['condition']['text']}")
print(f"Temperature: {weather['current']['temp_c']}°C / {weather['current']['temp_f']}°F")
print(f"Humidity: {weather['current']['humidity']}%")
print(f"Wind: {weather['current']['wind_kph']} kph, {weather['current']['wind_dir']}")
```

#### `get_air_quality`

```python
get_air_quality(location: str) -> Dict[str, Any]
```

Get air quality information for a location.

**Parameters:**
- `location`: Location name or coordinates

**Returns:**
- Dictionary with air quality information:
  - `co`: Carbon monoxide level
  - `o3`: Ozone level
  - `no2`: Nitrogen dioxide level
  - `so2`: Sulfur dioxide level
  - `pm2_5`: PM2.5 level
  - `pm10`: PM10 level
  - `us-epa-index`: US EPA air quality index
  - `gb-defra-index`: UK DEFRA air quality index

**Raises:**
- `NetworkError`: If API request fails
- `APIError`: If API returns an error
- `MissingAPIKeyError`: If API key is not found

**Example:**
```python
air_quality = context.weather.get_air_quality(location="Los Angeles")
print(f"Air Quality in Los Angeles:")
print(f"PM2.5: {air_quality['pm2_5']}")
print(f"EPA Index: {air_quality['us-epa-index']}")
```

#### `get_forecast`

```python
get_forecast(location: str, days: int = 3) -> Dict[str, Any]
```

Get weather forecast for a location.

**Parameters:**
- `location`: Location name or coordinates
- `days`: Number of days to forecast (1-10)

**Returns:**
- Dictionary with forecast information:
  - `location`: Location information
  - `current`: Current weather conditions
  - `forecast`: List of forecast days, each containing:
    - `date`: Forecast date
    - `max_temp_c`: Maximum temperature in Celsius
    - `min_temp_c`: Minimum temperature in Celsius
    - `avg_temp_c`: Average temperature in Celsius
    - `max_temp_f`: Maximum temperature in Fahrenheit
    - `min_temp_f`: Minimum temperature in Fahrenheit
    - `avg_temp_f`: Average temperature in Fahrenheit
    - `condition`: Weather condition text
    - `uv`: UV index

**Raises:**
- `NetworkError`: If API request fails
- `APIError`: If API returns an error
- `MissingAPIKeyError`: If API key is not found
- `ValueError`: If days is not between 1 and 10

**Example:**
```python
forecast = context.weather.get_forecast(location="Tokyo", days=5)
print(f"Weather forecast for {forecast['location']['name']}:")

for day in forecast["forecast"]:
    print(f"Date: {day['date']}")
    print(f"  Condition: {day['condition']}")
    print(f"  Temperature: {day['min_temp_c']}°C to {day['max_temp_c']}°C")
```

#### `interpret_condition`

```python
interpret_condition(condition_code: int) -> str
```

Interpret a weather condition code.

**Parameters:**
- `condition_code`: Weather condition code from API

**Returns:**
- Human-readable description of the condition

**Example:**
```python
condition_code = weather['current']['condition']['code']
description = context.weather.interpret_condition(condition_code)
print(f"Weather condition: {description}")
```

#### `get_outdoor_activity_recommendation`

```python
get_outdoor_activity_recommendation(weather_data: Dict[str, Any]) -> str
```

Get a recommendation for outdoor activities based on weather.

**Parameters:**
- `weather_data`: Weather data from the current() method

**Returns:**
- Recommendation string

**Example:**
```python
weather = context.weather.current(location="Berlin")
recommendation = context.weather.get_outdoor_activity_recommendation(weather)
print(f"Outdoor activity recommendation: {recommendation}")
```

## Utility Functions

The weather module provides utility functions for working with weather data.

### `celsius_to_fahrenheit`

```python
celsius_to_fahrenheit(celsius: float) -> float
```

Convert temperature from Celsius to Fahrenheit.

**Parameters:**
- `celsius`: Temperature in Celsius

**Returns:**
- Temperature in Fahrenheit

**Example:**
```python
from contextual_cc.weather.utils import celsius_to_fahrenheit

temp_f = celsius_to_fahrenheit(20)
print(f"20°C = {temp_f}°F")  # "20°C = 68.0°F"
```

### `fahrenheit_to_celsius`

```python
fahrenheit_to_celsius(fahrenheit: float) -> float
```

Convert temperature from Fahrenheit to Celsius.

**Parameters:**
- `fahrenheit`: Temperature in Fahrenheit

**Returns:**
- Temperature in Celsius

**Example:**
```python
from contextual_cc.weather.utils import fahrenheit_to_celsius

temp_c = fahrenheit_to_celsius(68)
print(f"68°F = {temp_c}°C")  # "68°F = 20.0°C"
```

### `get_comfort_level`

```python
get_comfort_level(temp_c: float, humidity: float) -> str
```

Get comfort level based on temperature and humidity.

**Parameters:**
- `temp_c`: Temperature in Celsius
- `humidity`: Relative humidity percentage

**Returns:**
- Comfort level description

**Example:**
```python
from contextual_cc.weather.utils import get_comfort_level

comfort = get_comfort_level(25, 70)
print(f"Comfort level: {comfort}")  # "Warm and humid"
```

### `calculate_heat_index`

```python
calculate_heat_index(temp_c: float, humidity: float) -> float
```

Calculate the heat index (feels like temperature) in Celsius.

**Parameters:**
- `temp_c`: Temperature in Celsius
- `humidity`: Relative humidity percentage

**Returns:**
- Heat index in Celsius

**Example:**
```python
from contextual_cc.weather.utils import calculate_heat_index

heat_index = calculate_heat_index(30, 80)
print(f"Temperature: 30°C, Humidity: 80%")
print(f"Feels like: {heat_index:.1f}°C")
```

### `get_wind_direction_text`

```python
get_wind_direction_text(degrees: float) -> str
```

Convert wind direction in degrees to cardinal direction text.

**Parameters:**
- `degrees`: Wind direction in degrees

**Returns:**
- Cardinal direction (e.g., 'N', 'NE', 'E', etc.)

**Example:**
```python
from contextual_cc.weather.utils import get_wind_direction_text

direction = get_wind_direction_text(45)
print(f"Wind direction at 45°: {direction}")  # "NE"
```

### `get_uv_index_description`

```python
get_uv_index_description(uv_index: float) -> str
```

Get a description of UV index value.

**Parameters:**
- `uv_index`: UV index value

**Returns:**
- Description of UV index risk level

**Example:**
```python
from contextual_cc.weather.utils import get_uv_index_description

description = get_uv_index_description(7)
print(f"UV index 7: {description}")  # "High"
```