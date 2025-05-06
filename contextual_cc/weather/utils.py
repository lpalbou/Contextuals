"""Utility functions for weather module."""

from typing import Dict, Any, List, Tuple, Optional


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert temperature from Celsius to Fahrenheit.
    
    Args:
        celsius: Temperature in Celsius.
        
    Returns:
        Temperature in Fahrenheit.
    """
    return (celsius * 9/5) + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert temperature from Fahrenheit to Celsius.
    
    Args:
        fahrenheit: Temperature in Fahrenheit.
        
    Returns:
        Temperature in Celsius.
    """
    return (fahrenheit - 32) * 5/9


def get_comfort_level(temp_c: float, humidity: float) -> str:
    """Get comfort level based on temperature and humidity.
    
    Args:
        temp_c: Temperature in Celsius.
        humidity: Relative humidity percentage.
        
    Returns:
        Comfort level description.
    """
    if temp_c < 0:
        return "Very cold"
    elif temp_c < 10:
        return "Cold"
    elif temp_c < 20:
        # For cool temperatures, humidity doesn't matter as much
        return "Cool"
    elif temp_c < 25:
        if humidity < 30:
            return "Comfortable and dry"
        elif humidity < 60:
            return "Comfortable"
        else:
            return "Comfortable but humid"
    elif temp_c < 30:
        if humidity < 30:
            return "Warm and dry"
        elif humidity < 60:
            return "Warm"
        else:
            return "Warm and humid"
    elif temp_c < 35:
        if humidity < 30:
            return "Hot and dry"
        elif humidity < 60:
            return "Hot"
        else:
            return "Hot and humid"
    else:
        if humidity < 30:
            return "Very hot and dry"
        elif humidity < 60:
            return "Very hot"
        else:
            return "Very hot and humid"


def calculate_heat_index(temp_c: float, humidity: float) -> float:
    """Calculate the heat index (feels like temperature) in Celsius.
    
    The heat index combines temperature and humidity to determine the
    perceived temperature.
    
    Args:
        temp_c: Temperature in Celsius.
        humidity: Relative humidity percentage.
        
    Returns:
        Heat index in Celsius.
    """
    # Convert to Fahrenheit for the standard heat index formula
    temp_f = celsius_to_fahrenheit(temp_c)
    
    # The Rothfusz regression formula
    if temp_f < 80:
        # Heat index not applicable for lower temperatures
        return temp_c
    
    # Calculate heat index in Fahrenheit
    hi = -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
    hi -= 0.22475541 * temp_f * humidity
    hi -= 0.00683783 * temp_f * temp_f
    hi -= 0.05481717 * humidity * humidity
    hi += 0.00122874 * temp_f * temp_f * humidity
    hi += 0.00085282 * temp_f * humidity * humidity
    hi -= 0.00000199 * temp_f * temp_f * humidity * humidity
    
    # Convert back to Celsius
    return fahrenheit_to_celsius(hi)


def get_wind_direction_text(degrees: float) -> str:
    """Convert wind direction in degrees to cardinal direction text.
    
    Args:
        degrees: Wind direction in degrees.
        
    Returns:
        Cardinal direction (e.g., 'N', 'NE', 'E', etc.).
    """
    directions = [
        ("N", 0), 
        ("NNE", 22.5), 
        ("NE", 45), 
        ("ENE", 67.5), 
        ("E", 90),
        ("ESE", 112.5), 
        ("SE", 135), 
        ("SSE", 157.5), 
        ("S", 180),
        ("SSW", 202.5), 
        ("SW", 225), 
        ("WSW", 247.5), 
        ("W", 270),
        ("WNW", 292.5), 
        ("NW", 315), 
        ("NNW", 337.5)
    ]
    
    # Normalize the angle to be between 0 and 360
    normalized_degrees = degrees % 360
    
    # Find the closest direction
    index = round(normalized_degrees / 22.5) % 16
    
    return directions[index][0]


def get_uv_index_description(uv_index: float) -> str:
    """Get a description of UV index value.
    
    Args:
        uv_index: UV index value.
        
    Returns:
        Description of UV index risk level.
    """
    if uv_index < 3:
        return "Low"
    elif uv_index < 6:
        return "Moderate"
    elif uv_index < 8:
        return "High"
    elif uv_index < 11:
        return "Very High"
    else:
        return "Extreme"
