"""Utility functions for location module."""

import math
from typing import Tuple, Optional, List, Dict, Any


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "km") -> float:
    """Calculate the great-circle distance between two points on Earth.
    
    Uses the Haversine formula.
    
    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.
        unit: Distance unit ('km' for kilometers or 'mi' for miles).
        
    Returns:
        Distance in the specified unit.
        
    Raises:
        ValueError: If unit is not 'km' or 'mi'.
    """
    # Validate unit
    if unit not in ["km", "mi"]:
        raise ValueError("Unit must be 'km' or 'mi'")
    
    # Earth radius in kilometers
    earth_radius_km = 6371.0
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = earth_radius_km * c
    
    # Convert to requested unit
    if unit == "mi":
        return distance_km * 0.621371  # Convert km to miles
    else:
        return distance_km


def get_cardinal_direction(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Get the cardinal direction (N, NE, E, etc.) from point 1 to point 2.
    
    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.
        
    Returns:
        Cardinal direction as a string.
    """
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Calculate bearing
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing_rad = math.atan2(y, x)
    
    # Convert to degrees
    bearing_deg = math.degrees(bearing_rad)
    # Normalize to 0-360
    bearing_deg = (bearing_deg + 360) % 360
    
    # Convert to cardinal direction
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    index = round(bearing_deg / 22.5) % 16
    return directions[index]


def parse_coordinates(coord_str: str) -> Tuple[float, float]:
    """Parse a string representation of coordinates.
    
    Supports various formats:
    - "latitude,longitude" (e.g., "40.7128,-74.0060")
    - "latitude longitude" (e.g., "40.7128 -74.0060")
    - DMS format (e.g., "40°42'46.8\"N 74°0'21.6\"W")
    
    Args:
        coord_str: String representation of coordinates.
        
    Returns:
        Tuple of (latitude, longitude) as floats.
        
    Raises:
        ValueError: If the string cannot be parsed.
    """
    # Try comma-separated format
    if "," in coord_str:
        parts = coord_str.split(",")
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return (lat, lon)
            except ValueError:
                pass
    
    # Try space-separated format
    parts = coord_str.strip().split()
    if len(parts) == 2:
        try:
            lat = float(parts[0])
            lon = float(parts[1])
            return (lat, lon)
        except ValueError:
            pass
    
    # Try DMS format
    # This is a simplified parser and might not handle all DMS formats
    if "°" in coord_str:
        try:
            # Extract numeric parts and hemisphere indicators
            lat_parts = coord_str.split()[0]
            lon_parts = coord_str.split()[1]
            
            # Parse latitude
            lat_deg = float(lat_parts.split("°")[0])
            lat_min = float(lat_parts.split("°")[1].split("'")[0])
            lat_sec = float(lat_parts.split("'")[1].split('"')[0])
            lat_hem = lat_parts[-1]  # N or S
            
            lat = lat_deg + lat_min/60 + lat_sec/3600
            if lat_hem == "S":
                lat = -lat
            
            # Parse longitude
            lon_deg = float(lon_parts.split("°")[0])
            lon_min = float(lon_parts.split("°")[1].split("'")[0])
            lon_sec = float(lon_parts.split("'")[1].split('"')[0])
            lon_hem = lon_parts[-1]  # E or W
            
            lon = lon_deg + lon_min/60 + lon_sec/3600
            if lon_hem == "W":
                lon = -lon
            
            return (lat, lon)
        except (ValueError, IndexError):
            pass
    
    raise ValueError(f"Could not parse coordinates: {coord_str}")


def format_coordinates(latitude: float, longitude: float, format_type: str = "decimal") -> str:
    """Format coordinates in different formats.
    
    Args:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.
        format_type: Format type ('decimal', 'dms', or 'dm').
        
    Returns:
        Formatted coordinate string.
        
    Raises:
        ValueError: If format_type is not recognized.
    """
    if format_type == "decimal":
        return f"{latitude:.6f}, {longitude:.6f}"
    
    elif format_type == "dms":
        # Convert decimal degrees to degrees, minutes, seconds
        lat_deg = int(abs(latitude))
        lat_min = int((abs(latitude) - lat_deg) * 60)
        lat_sec = ((abs(latitude) - lat_deg - lat_min/60) * 3600)
        lat_hem = "N" if latitude >= 0 else "S"
        
        lon_deg = int(abs(longitude))
        lon_min = int((abs(longitude) - lon_deg) * 60)
        lon_sec = ((abs(longitude) - lon_deg - lon_min/60) * 3600)
        lon_hem = "E" if longitude >= 0 else "W"
        
        return f"{lat_deg}°{lat_min}'{lat_sec:.1f}\"{lat_hem} {lon_deg}°{lon_min}'{lon_sec:.1f}\"{lon_hem}"
    
    elif format_type == "dm":
        # Convert decimal degrees to degrees and decimal minutes
        lat_deg = int(abs(latitude))
        lat_min = (abs(latitude) - lat_deg) * 60
        lat_hem = "N" if latitude >= 0 else "S"
        
        lon_deg = int(abs(longitude))
        lon_min = (abs(longitude) - lon_deg) * 60
        lon_hem = "E" if longitude >= 0 else "W"
        
        return f"{lat_deg}°{lat_min:.4f}'{lat_hem} {lon_deg}°{lon_min:.4f}'{lon_hem}"
    
    else:
        raise ValueError(f"Unrecognized format type: {format_type}")


def is_valid_coordinate(latitude: float, longitude: float) -> bool:
    """Check if coordinates are valid.
    
    Args:
        latitude: Latitude in decimal degrees.
        longitude: Longitude in decimal degrees.
        
    Returns:
        True if coordinates are valid, False otherwise.
    """
    return -90 <= latitude <= 90 and -180 <= longitude <= 180
