# Contextuals Core API Reference

This document provides detailed API reference for the core components of Contextuals.

## Table of Contents
- [Contextuals](#contextuals)
- [Config](#config)
- [Cache](#cache)
- [Exceptions](#exceptions)

## Contextuals

The main entry point for the library.

### Constructor

```python
Contextuals(**kwargs)
```

**Parameters:**
- `**kwargs`: Configuration options to override defaults. See [Configuration Options](#configuration-options) for details.

### Properties

| Property | Return Type | Description |
|----------|-------------|-------------|
| `time` | `TimeProvider` | Access time-related contextual information |
| `weather` | `WeatherProvider` | Access weather-related contextual information |
| `location` | `LocationProvider` | Access location-related contextual information |

### Methods

#### `update_config`

```python
update_config(**kwargs)
```

Update configuration options.

**Parameters:**
- `**kwargs`: Configuration options to update

**Example:**
```python
context = Contextuals()
context.update_config(cache_duration=600, use_fallback=False)
```

#### `set_api_key`

```python
set_api_key(service: str, api_key: str)
```

Set API key for a specific service.

**Parameters:**
- `service`: Service name (e.g., 'weather', 'location')
- `api_key`: The API key

**Example:**
```python
context = Contextuals()
context.set_api_key("weather", "your_weather_api_key")
```

#### `clear_cache`

```python
clear_cache()
```

Clear all cached data.

**Example:**
```python
context = Contextuals()
context.clear_cache()
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cache_enabled` | `bool` | `True` | Whether caching is enabled |
| `cache_duration` | `int` | `300` | Default cache duration in seconds (5 minutes) |
| `time_api_url` | `str` | `"http://worldtimeapi.org/api/ip"` | URL for time API |
| `weather_api_url` | `str` | `"https://api.weatherapi.com/v1/current.json"` | URL for weather API |
| `location_api_url` | `str` | `"https://nominatim.openstreetmap.org/search"` | URL for location API |
| `use_fallback` | `bool` | `True` | Whether to use fallbacks when APIs are unavailable |
| `weather_api_key` | `str` | `None` | API key for weather service |
| `location_api_key` | `str` | `None` | API key for location service |
| `time_auto_sync` | `bool` | `True` | Whether to automatically sync time with API |
| `time_sync_interval` | `int` | `300` | Time sync interval in seconds (5 minutes) |

## Config

Manages configuration options.

### Constructor

```python
Config(**kwargs)
```

**Parameters:**
- `**kwargs`: Configuration options to override defaults

### Methods

#### `get`

```python
get(key: str, default: Any = None) -> Any
```

Get a configuration value.

**Parameters:**
- `key`: The configuration key to retrieve
- `default`: Default value if key is not found

**Returns:**
- Configuration value or default

#### `set`

```python
set(key: str, value: Any) -> None
```

Set a configuration value.

**Parameters:**
- `key`: The configuration key to set
- `value`: The value to set

#### `update`

```python
update(config_dict: Dict[str, Any]) -> None
```

Update multiple configuration values.

**Parameters:**
- `config_dict`: Dictionary of configuration values to update

#### `get_api_key`

```python
get_api_key(service: str) -> Optional[str]
```

Get API key for a specific service.

**Parameters:**
- `service`: Service name (e.g., 'weather', 'location')

**Returns:**
- API key if available, None otherwise

#### `set_api_key`

```python
set_api_key(service: str, api_key: str) -> None
```

Set API key for a specific service.

**Parameters:**
- `service`: Service name (e.g., 'weather', 'location')
- `api_key`: The API key value

## Cache

Provides time-based caching.

### Constructor

```python
Cache(default_ttl: int = 300)
```

**Parameters:**
- `default_ttl`: Default time-to-live for cache entries in seconds

### Methods

#### `get`

```python
get(key: str) -> Optional[Any]
```

Get a value from the cache if it exists and is not expired.

**Parameters:**
- `key`: Cache key

**Returns:**
- Cached value or None if not found or expired

#### `set`

```python
set(key: str, value: Any, ttl: Optional[int] = None) -> None
```

Set a value in the cache with a time-to-live.

**Parameters:**
- `key`: Cache key
- `value`: Value to cache
- `ttl`: Time-to-live in seconds. Defaults to the cache default_ttl.

#### `invalidate`

```python
invalidate(key: str) -> None
```

Invalidate a cache entry.

**Parameters:**
- `key`: Cache key to invalidate

#### `clear`

```python
clear() -> None
```

Clear all cache entries.

### `cached` Decorator

```python
@cached(ttl: Optional[int] = None)
```

Decorator for caching function results.

**Parameters:**
- `ttl`: Time-to-live in seconds. If None, uses the cache default.

**Example:**
```python
from contextuals.core.cache import cached

@cached(ttl=300)  # Cache for 5 minutes
def expensive_function(param1, param2):
    # ... complex computation ...
    return result
```

## Exceptions

Custom exceptions used in Contextuals.

### `ContextualsError`

Base exception for all Contextuals exceptions.

### `APIError`

Error when interacting with external APIs.

### `ConfigurationError`

Error in configuration.

### `MissingAPIKeyError`

Missing required API key.

### `NetworkError`

Network-related error.

### `FallbackError`

Error when all fallback mechanisms fail.