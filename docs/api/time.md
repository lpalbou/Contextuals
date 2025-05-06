# Time API Reference

This document provides detailed API reference for the time context module in Contextual-CC.

## Table of Contents
- [TimeProvider](#timeprovider)
- [Utility Functions](#utility-functions)

## TimeProvider

The TimeProvider class provides time-related contextual information.

### Constructor

```python
TimeProvider(config: Config, cache: Cache)
```

**Parameters:**
- `config`: Configuration instance
- `cache`: Cache instance

**Note:** You typically won't instantiate this class directly but access it through the `ContextualCC` interface.

### Methods

#### `now`

```python
now(timezone: Optional[str] = None) -> datetime.datetime
```

Get the current time, using the synchronized offset when available.

**Parameters:**
- `timezone`: Optional timezone name (e.g., 'UTC', 'America/New_York'). If None, returns in the UTC timezone.

**Returns:**
- Current datetime in the specified timezone

**Raises:**
- `FallbackError`: If sync failed and fallback is disabled

**Example:**
```python
from contextual_cc import ContextualCC

context = ContextualCC()
# Get current time in UTC
now_utc = context.time.now()
# Get current time in New York
now_ny = context.time.now(timezone="America/New_York")
```

#### `get_timezone_info`

```python
get_timezone_info(timezone: str) -> Dict[str, Any]
```

Get information about a timezone.

**Parameters:**
- `timezone`: Timezone name (e.g., 'UTC', 'America/New_York')

**Returns:**
- Dictionary with timezone information:
  - `name`: Timezone name
  - `offset`: Offset from UTC in hours
  - `dst`: Whether daylight saving time is in effect
  - `current_time`: Current time in this timezone

**Raises:**
- `ValueError`: If timezone is invalid

**Example:**
```python
timezone_info = context.time.get_timezone_info("Europe/Paris")
print(f"Paris is UTC{'+' if timezone_info['offset'] >= 0 else ''}{timezone_info['offset']}")
print(f"DST in effect: {timezone_info['dst']}")
```

#### `get_offset`

```python
get_offset() -> float
```

Get the current offset between local time and server time.

**Returns:**
- Offset in seconds

**Example:**
```python
offset = context.time.get_offset()
print(f"Time offset from server: {offset} seconds")
```

#### `format_time`

```python
format_time(dt: Optional[datetime.datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str
```

Format a datetime object as a string.

**Parameters:**
- `dt`: Datetime to format. If None, uses the current time.
- `fmt`: Format string (strftime format)

**Returns:**
- Formatted time string

**Example:**
```python
# Format current time
formatted = context.time.format_time(fmt="%Y-%m-%d %H:%M:%S")
print(f"Current time: {formatted}")

# Format a specific datetime
from datetime import datetime
dt = datetime(2023, 1, 1, 12, 0, 0)
formatted = context.time.format_time(dt, fmt="%A, %B %d, %Y")
print(f"Formatted date: {formatted}")
```

#### `force_sync`

```python
force_sync() -> bool
```

Force a synchronization with the time API.

**Returns:**
- True if sync was successful, False otherwise

**Example:**
```python
success = context.time.force_sync()
if success:
    print("Successfully synchronized time with external API")
else:
    print("Time synchronization failed")
```

## Utility Functions

The time module provides utility functions for working with time.

### `parse_datetime`

```python
parse_datetime(dt_str: str) -> datetime.datetime
```

Parse a string into a datetime object. Supports various common formats.

**Parameters:**
- `dt_str`: String representation of a datetime

**Returns:**
- Datetime object

**Raises:**
- `ValueError`: If the string cannot be parsed

**Example:**
```python
from contextual_cc.time.utils import parse_datetime

dt = parse_datetime("2023-01-01T12:00:00Z")
print(f"Parsed datetime: {dt}")
```

### `get_unix_timestamp`

```python
get_unix_timestamp(dt: Optional[datetime.datetime] = None) -> float
```

Convert a datetime to a Unix timestamp.

**Parameters:**
- `dt`: Datetime object. If None, uses the current time.

**Returns:**
- Unix timestamp (seconds since epoch)

**Example:**
```python
from contextual_cc.time.utils import get_unix_timestamp
from datetime import datetime

# Get timestamp for now
timestamp_now = get_unix_timestamp()
print(f"Current timestamp: {timestamp_now}")

# Get timestamp for a specific datetime
dt = datetime(2023, 1, 1, 12, 0, 0)
timestamp = get_unix_timestamp(dt)
print(f"Timestamp for {dt}: {timestamp}")
```

### `format_duration`

```python
format_duration(seconds: float) -> str
```

Format a duration in seconds to a human-readable string.

**Parameters:**
- `seconds`: Duration in seconds

**Returns:**
- Human-readable duration string

**Example:**
```python
from contextual_cc.time.utils import format_duration

duration = format_duration(3665)  # 1 hour, 1 minute, 5 seconds
print(f"Duration: {duration}")  # "1 hours, 1 minutes"
```

### `get_day_period`

```python
get_day_period(dt: Optional[datetime.datetime] = None) -> str
```

Get the period of the day (morning, afternoon, evening, night).

**Parameters:**
- `dt`: Datetime object. If None, uses the current time.

**Returns:**
- Period of the day as a string ('morning', 'afternoon', 'evening', or 'night')

**Example:**
```python
from contextual_cc.time.utils import get_day_period
from datetime import datetime

# Get current period of the day
period = get_day_period()
print(f"Current period: {period}")

# Get period for a specific time
dt = datetime(2023, 1, 1, 8, 0, 0)
period = get_day_period(dt)
print(f"Period at 8 AM: {period}")  # "morning"
```