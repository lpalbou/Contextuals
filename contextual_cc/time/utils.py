"""Utility functions for time module."""

import datetime
from typing import Optional, Union, Tuple


def parse_datetime(dt_str: str) -> datetime.datetime:
    """Parse a string into a datetime object.
    
    Supports various common formats.
    
    Args:
        dt_str: String representation of a datetime.
        
    Returns:
        Datetime object.
        
    Raises:
        ValueError: If the string cannot be parsed.
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds
        "%Y-%m-%dT%H:%M:%SZ",      # ISO 8601
        "%Y-%m-%d %H:%M:%S",       # Common format
        "%Y-%m-%d",               # Date only
    ]
    
    for fmt in formats:
        try:
            return datetime.datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse datetime string: {dt_str}")


def get_unix_timestamp(dt: Optional[datetime.datetime] = None) -> float:
    """Convert a datetime to a Unix timestamp.
    
    Args:
        dt: Datetime object. If None, uses the current time.
        
    Returns:
        Unix timestamp (seconds since epoch).
    """
    if dt is None:
        return datetime.datetime.now().timestamp()
    
    return dt.timestamp()


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Human-readable duration string.
    """
    if seconds < 60:
        return f"{int(seconds)} seconds"
    
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)} minutes, {int(seconds)} seconds"
    
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{int(hours)} hours, {int(minutes)} minutes"
    
    days, hours = divmod(hours, 24)
    return f"{int(days)} days, {int(hours)} hours"


def get_day_period(dt: Optional[datetime.datetime] = None) -> str:
    """Get the period of the day (morning, afternoon, evening, night).
    
    Args:
        dt: Datetime object. If None, uses the current time.
        
    Returns:
        Period of the day as a string.
    """
    if dt is None:
        dt = datetime.datetime.now()
    
    hour = dt.hour
    
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"
