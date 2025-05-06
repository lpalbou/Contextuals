# Location API Reference

This document provides detailed API reference for the location context module in Contextual-CC.

## Table of Contents
- [LocationProvider](#locationprovider)
- [Utility Functions](#utility-functions)

## LocationProvider

The LocationProvider class provides location-related contextual information.

### Constructor

```python
LocationProvider(config: Config, cache: Cache)
```

**Parameters:**
- `config`: Configuration instance
- `cache`: Cache instance

**Note:** You typically won't instantiate this class directly but access it through the `ContextualCC` interface.

### Methods

#### `get`

```python
get(location: str) -> Dict[str, Any]
```

Get location information by name or address.

**Parameters:**
- `location`: Location name or address

**Returns:**
- Dictionary with location information:
  - `name`: Full name/address of the location
  - `coordinates`: Latitude and longitude
  - `address`: Structured address components
  - `type`: Location type
  - `importance`: Importance rank
  - `osm_id`: OpenStreetMap ID

**Raises:**
- `NetworkError`: If API request fails and no fallback is available
- `APIError`: If API returns an error

**Example:**
```python
from contextual_cc import ContextualCC

context = ContextualCC()
location = context.location.get("Sydney Opera House")

print(f"Location: {location['name']}")
print(f"Coordinates: {location['coordinates']['latitude']}, {location['coordinates']['longitude']}")
print(f"Country: {location['address']['country']}")
```

#### `reverse_geocode`

```python
reverse_geocode(latitude: float, longitude: float) -> Dict[str, Any]
```

Convert coordinates to a location name and address.

**Parameters:**
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate

**Returns:**
- Dictionary with location information (same structure as `get` method)

**Raises:**
- `NetworkError`: If API request fails
- `APIError`: If API returns an error

**Example:**
```python
# Eiffel Tower coordinates
location = context.location.reverse_geocode(latitude=48.8584, longitude=2.2945)
print(f"Found location: {location['name']}")
print(f"Address: {location['address']['city']}, {location['address']['country']}")
```

#### `get_timezone`

```python
get_timezone(latitude: float, longitude: float) -> Dict[str, Any]
```

Get timezone information for coordinates.

**Parameters:**
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate

**Returns:**
- Dictionary with timezone information:
  - `timezone`: Timezone identifier
  - `coordinates`: Input coordinates
  - `offset_hours`: Hours offset from UTC (if approximate)
  - `approximate`: Boolean indicating if the timezone is approximate

**Raises:**
- `NetworkError`: If API request fails
- `APIError`: If API returns an error

**Example:**
```python
# Get timezone for San Francisco
timezone = context.location.get_timezone(latitude=37.7749, longitude=-122.4194)
print(f"Timezone: {timezone['timezone']}")
```

#### `calculate_distance`

```python
calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "km") -> float
```

Calculate distance between two coordinates.

**Parameters:**
- `lat1`: Latitude of point 1
- `lon1`: Longitude of point 1
- `lat2`: Latitude of point 2
- `lon2`: Longitude of point 2
- `unit`: Distance unit ('km' for kilometers or 'mi' for miles)

**Returns:**
- Distance in the specified unit

**Raises:**
- `ValueError`: If unit is not 'km' or 'mi'

**Example:**
```python
# Distance between New York and Los Angeles
distance = context.location.calculate_distance(
    lat1=40.7128, lon1=-74.0060,  # New York
    lat2=34.0522, lon2=-118.2437,  # Los Angeles
    unit="km"
)
print(f"Distance: {distance:.1f} km")

# Same distance in miles
distance_mi = context.location.calculate_distance(
    lat1=40.7128, lon1=-74.0060,
    lat2=34.0522, lon2=-118.2437,
    unit="mi"
)
print(f"Distance: {distance_mi:.1f} miles")
```

#### `get_nearby_locations`

```python
get_nearby_locations(latitude: float, longitude: float, radius: float, limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]
```

Find nearby locations within a radius.

**Parameters:**
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate
- `radius`: Search radius in kilometers
- `limit`: Maximum number of results
- `category`: Optional category filter (e.g., 'restaurant', 'hotel')

**Returns:**
- List of nearby locations, each with the same structure as `get` method results,
  plus a `distance` field with the distance from the center point

**Raises:**
- `NetworkError`: If API request fails
- `APIError`: If API returns an error

**Example:**
```python
# Find restaurants near Central Park
nearby = context.location.get_nearby_locations(
    latitude=40.7812, longitude=-73.9665,  # Central Park
    radius=1.0,  # 1 km radius
    limit=5,
    category="restaurant"
)

print(f"Found {len(nearby)} nearby restaurants:")
for place in nearby:
    print(f"- {place['name']} ({place['distance']:.2f} km)")
```

## Utility Functions

The location module provides utility functions for working with location data.

### `calculate_haversine_distance`

```python
calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "km") -> float
```

Calculate the great-circle distance between two points on Earth.

**Parameters:**
- `lat1`: Latitude of point 1 in decimal degrees
- `lon1`: Longitude of point 1 in decimal degrees
- `lat2`: Latitude of point 2 in decimal degrees
- `lon2`: Longitude of point 2 in decimal degrees
- `unit`: Distance unit ('km' for kilometers or 'mi' for miles)

**Returns:**
- Distance in the specified unit

**Raises:**
- `ValueError`: If unit is not 'km' or 'mi'

**Example:**
```python
from contextual_cc.location.utils import calculate_haversine_distance

distance = calculate_haversine_distance(
    lat1=51.5074, lon1=-0.1278,  # London
    lat2=48.8566, lon2=2.3522,    # Paris
    unit="km"
)
print(f"Distance from London to Paris: {distance:.1f} km")
```

### `get_cardinal_direction`

```python
get_cardinal_direction(lat1: float, lon1: float, lat2: float, lon2: float) -> str
```

Get the cardinal direction (N, NE, E, etc.) from point 1 to point 2.

**Parameters:**
- `lat1`: Latitude of point 1 in decimal degrees
- `lon1`: Longitude of point 1 in decimal degrees
- `lat2`: Latitude of point 2 in decimal degrees
- `lon2`: Longitude of point 2 in decimal degrees

**Returns:**
- Cardinal direction as a string

**Example:**
```python
from contextual_cc.location.utils import get_cardinal_direction

direction = get_cardinal_direction(
    lat1=51.5074, lon1=-0.1278,  # London
    lat2=48.8566, lon2=2.3522,    # Paris
)
print(f"Direction from London to Paris: {direction}")
```

### `parse_coordinates`

```python
parse_coordinates(coord_str: str) -> Tuple[float, float]
```

Parse a string representation of coordinates.

**Parameters:**
- `coord_str`: String representation of coordinates

**Returns:**
- Tuple of (latitude, longitude) as floats

**Raises:**
- `ValueError`: If the string cannot be parsed

**Example:**
```python
from contextual_cc.location.utils import parse_coordinates

# Parse comma-separated coordinates
lat, lon = parse_coordinates("40.7128,-74.0060")
print(f"Latitude: {lat}, Longitude: {lon}")

# Parse space-separated coordinates
lat, lon = parse_coordinates("40.7128 -74.0060")
print(f"Latitude: {lat}, Longitude: {lon}")

# Parse DMS format
lat, lon = parse_coordinates('40°42\'46.8"N 74°0\'21.6"W')
print(f"Latitude: {lat}, Longitude: {lon}")
```

### `format_coordinates`

```python
format_coordinates(latitude: float, longitude: float, format_type: str = "decimal") -> str
```

Format coordinates in different formats.

**Parameters:**
- `latitude`: Latitude in decimal degrees
- `longitude`: Longitude in decimal degrees
- `format_type`: Format type ('decimal', 'dms', or 'dm')

**Returns:**
- Formatted coordinate string

**Raises:**
- `ValueError`: If format_type is not recognized

**Example:**
```python
from contextual_cc.location.utils import format_coordinates

# Format as decimal degrees
decimal = format_coordinates(40.7128, -74.0060, format_type="decimal")
print(f"Decimal: {decimal}")  # "40.712800, -74.006000"

# Format as degrees, minutes, seconds
dms = format_coordinates(40.7128, -74.0060, format_type="dms")
print(f"DMS: {dms}")  # "40°42'46.1"N 74°0'21.6"W"

# Format as degrees, decimal minutes
dm = format_coordinates(40.7128, -74.0060, format_type="dm")
print(f"DM: {dm}")  # "40°42.7680'N 74°0.3600'W"
```

### `is_valid_coordinate`

```python
is_valid_coordinate(latitude: float, longitude: float) -> bool
```

Check if coordinates are valid.

**Parameters:**
- `latitude`: Latitude in decimal degrees
- `longitude`: Longitude in decimal degrees

**Returns:**
- True if coordinates are valid, False otherwise

**Example:**
```python
from contextual_cc.location.utils import is_valid_coordinate

print(is_valid_coordinate(40.7128, -74.0060))  # True
print(is_valid_coordinate(100, -74.0060))     # False (latitude > 90)
print(is_valid_coordinate(40.7128, -200))     # False (longitude < -180)
```