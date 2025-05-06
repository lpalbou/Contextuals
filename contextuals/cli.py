"""Command-line interface for Contextuals."""

import argparse
import datetime
import json
import sys
from typing import Dict, Any, Optional

from contextuals import Contextuals


def format_output(data: Dict[str, Any], format_type: str = "pretty") -> str:
    """Format output data based on format type.
    
    Args:
        data: Data to format
        format_type: Output format (pretty, json, compact)
        
    Returns:
        Formatted string
    """
    if format_type == "json":
        return json.dumps(data, indent=2)
    elif format_type == "compact":
        return json.dumps(data)
    else:  # pretty format
        return _pretty_format(data)


def _pretty_format(data: Dict[str, Any]) -> str:
    """Create a human-readable formatted output.
    
    Args:
        data: Data to format
        
    Returns:
        Pretty-formatted string
    """
    output = []
    
    # Handle timestamp
    if "timestamp" in data:
        output.append(f"Time: {data['timestamp']}")
    
    # Handle location
    if "location" in data:
        loc = data["location"]
        location_str = loc.get("name", "")
        if loc.get("country"):
            location_str += f", {loc['country']}"
        output.append(f"Location: {location_str}")
        if "lat" in loc and "lon" in loc:
            output.append(f"Coordinates: {loc.get('lat')}, {loc.get('lon')}")
    
    # Handle type
    if "type" in data:
        output.append(f"Data type: {data['type']}")
        
    # Handle error
    if "error" in data:
        output.append(f"Error: {data['error']}")
    
    # Special handling for all_context type - this is a container for multiple data types
    if data.get("type") == "all_context":
        output.append("\n=== All Available Context Information ===")
        
        # Format each section
        for section_name, section_data in data.items():
            if section_name in ["timestamp", "request_time", "type", "is_cached"]:
                continue
                
            # Format sections
            if isinstance(section_data, dict):
                # Handle unavailable sections gracefully
                if section_data.get("type", "").endswith("_unavailable"):
                    output.append(f"\n--- {section_name.upper()} ---")
                    output.append(f"Status: Unavailable")
                    if "data" in section_data and "reason" in section_data["data"]:
                        output.append(f"Reason: {section_data['data']['reason']}")
                    output.append("This information may be unavailable because of no internet connection or API issues.")
                # Handle error sections
                elif "error" in section_data:
                    output.append(f"\n--- {section_name.upper()} ---")
                    output.append(f"Status: Error")
                    output.append(f"Error: {section_data['error']}")
                # Normal sections
                else:
                    output.append(f"\n--- {section_name.upper()} ---")
                    output.append(_pretty_format(section_data))
        
        return "\n".join(output)
    
    # Handle actual data depending on type
    if "data" in data:
        data_content = data["data"]
        
        if data["type"] == "current_weather":
            temp = data_content.get("temp_c")
            condition = data_content.get("condition", {}).get("text", "Unknown")
            output.append(f"Temperature: {temp}°C")
            output.append(f"Condition: {condition}")
            output.append(f"Humidity: {data_content.get('humidity')}%")
            output.append(f"Wind: {data_content.get('wind_kph')} km/h {data_content.get('wind_dir', '')}")
            
        elif data["type"] == "air_quality":
            aqi = data_content.get("aqi", {})
            output.append(f"Air Quality: {aqi.get('description', 'Unknown')}")
            output.append(f"Health implications: {aqi.get('health_implications', 'Unknown')}")
            output.append(f"Recommendations: {data_content.get('recommendations', {}).get('general', 'No recommendations available')}")
            
        elif data["type"] == "astronomy":
            sun = data_content.get("sun", {})
            moon = data_content.get("moon", {})
            output.append(f"Sunrise: {sun.get('sunrise', 'Unknown')}")
            output.append(f"Sunset: {sun.get('sunset', 'Unknown')}")
            output.append(f"Day length: {sun.get('day_length', 'Unknown')}")
            output.append(f"Moon phase: {moon.get('phase_description', 'Unknown')}")
            
        elif data["type"] == "detailed_weather":
            uv = data_content.get("uv_index", {})
            vis = data_content.get("visibility", {})
            press = data_content.get("pressure", {})
            output.append(f"UV Index: {uv.get('value')} ({uv.get('category', 'Unknown')})")
            output.append(f"UV Risk: {uv.get('risk_level', 'Unknown')}")
            output.append(f"Visibility: {vis.get('kilometers')} km ({vis.get('description', 'Unknown')})")
            output.append(f"Pressure: {press.get('value')} hPa ({press.get('description', 'Unknown')})")
            
        elif data["type"] == "complete_weather_report":
            current = data_content.get("current", {})
            output.append(f"Temperature: {current.get('temp_c')}°C")
            output.append(f"Condition: {current.get('condition', {}).get('text', 'Unknown')}")
            
            # Add air quality if available
            air = data_content.get("air_quality", {})
            if air and "aqi" in air:
                output.append(f"Air Quality: {air.get('aqi', {}).get('description', 'Unknown')}")
            
            # Add astronomy if available
            astro = data_content.get("astronomy", {}).get("sun", {})
            if astro:
                output.append(f"Sunrise: {astro.get('sunrise', 'Unknown')}")
                output.append(f"Sunset: {astro.get('sunset', 'Unknown')}")
        
        elif data["type"] == "system_info":
            # Show system information
            os_info = data_content.get("os", {})
            output.append(f"OS: {os_info.get('system')} {os_info.get('release')}")
            output.append(f"Version: {os_info.get('version')}")
            output.append(f"Platform: {os_info.get('platform')}")
            output.append(f"Architecture: {os_info.get('architecture')}")
            output.append(f"Machine: {os_info.get('machine')}")
            
            if os_info.get("distribution"):
                output.append(f"Distribution: {os_info.get('distribution')} {os_info.get('distribution_version')}")
                
            if os_info.get("macos_version"):
                output.append(f"macOS Version: {os_info.get('macos_version')}")
                
            output.append(f"Hostname: {data_content.get('hostname')}")
            output.append(f"IP Address: {data_content.get('ip_address')}")
            
            # Environment
            env = data_content.get("environment", {})
            if env.get("term"):
                output.append(f"Terminal: {env.get('terminal', 'Unknown')} ({env.get('term', 'Unknown')})")
                
        elif data["type"] == "user_info":
            # Show user information
            output.append(f"Username: {data_content.get('username')}")
            
            if data_content.get("full_name"):
                output.append(f"Full Name: {data_content.get('full_name')}")
                
            output.append(f"Home Directory: {data_content.get('home_directory')}")
            
            if data_content.get("shell"):
                output.append(f"Shell: {data_content.get('shell')}")
                
            if data_content.get("language"):
                output.append(f"Language: {data_content.get('language')}")
                
            if data_content.get("uid") is not None:
                output.append(f"User ID: {data_content.get('uid')}")
                
        elif data["type"] == "logged_users":
            # Show logged users information
            output.append(f"Current user: {data_content.get('current_user', 'Unknown')}")
            
            # Show details about current user
            current_user_info = data_content.get("current_user_info", {})
            if current_user_info:
                if current_user_info.get("full_name"):
                    output.append(f"Full name: {current_user_info.get('full_name')}")
                output.append(f"Home directory: {current_user_info.get('home_directory', 'Unknown')}")
                output.append(f"Shell: {current_user_info.get('shell', 'Unknown')}")
                if current_user_info.get("email"):
                    output.append(f"Email: {current_user_info.get('email')}")
                    
            # Show total count of users
            if data_content.get("total_user_count"):
                output.append(f"\nTotal unique users: {data_content.get('total_user_count')}")
                
            # Show all logged users (limited info)
            all_users = data_content.get("all_logged_users", [])
            if all_users:
                output.append("\nLogged in users:")
                for user in all_users:
                    user_info = []
                    user_info.append(user.get('username', 'Unknown'))
                    if user.get("full_name"):
                        user_info.append(f"({user.get('full_name')})")
                    if user.get("email"):
                        user_info.append(f"<{user.get('email')}>")
                    output.append("  " + " ".join(user_info))
                
        elif data["type"] == "machine_info":
            # Show machine information
            output.append(f"Hostname: {data_content.get('hostname', 'Unknown')}")
            output.append(f"System: {data_content.get('system', 'Unknown')} {data_content.get('release', '')}")
            output.append(f"Platform: {data_content.get('platform', 'Unknown')}")
            output.append(f"Architecture: {data_content.get('architecture', 'Unknown')}")
            
            # Hardware identifiers
            if data_content.get("mac_address"):
                output.append(f"MAC Address: {data_content.get('mac_address')}")
            if data_content.get("hardware_uuid"):
                output.append(f"Hardware UUID: {data_content.get('hardware_uuid')}")
                
            # Detailed system info
            system_info = data_content.get("system_info", {})
            if system_info:
                output.append("\nSystem Information:")
                if system_info.get("system"):
                    output.append(f"OS: {system_info.get('system')}")
                if system_info.get("release"):
                    output.append(f"Kernel: {system_info.get('release')}")
                if system_info.get("version"):
                    output.append(f"Build: {system_info.get('version')}")
                if system_info.get("machine"):
                    output.append(f"Machine: {system_info.get('machine')}")
            
            # CPU information
            cpu = data_content.get("cpu", {})
            if cpu:
                output.append("\nCPU Information:")
                if cpu.get("model"):
                    output.append(f"Model: {cpu.get('model')}")
                if cpu.get("cores"):
                    output.append(f"Cores: {cpu.get('cores')}")
                if cpu.get("physical_processors"):
                    output.append(f"Physical processors: {cpu.get('physical_processors')}")
                if cpu.get("logical_processors"):
                    output.append(f"Logical processors: {cpu.get('logical_processors')}")
                    
            # Memory information
            memory = data_content.get("memory", {})
            if memory:
                output.append("\nMemory Information:")
                if memory.get("total_mb") is not None:
                    output.append(f"Total: {memory.get('total_mb')} MB")
                if memory.get("used_mb") is not None:
                    output.append(f"Used: {memory.get('used_mb')} MB")
                if memory.get("free_mb") is not None:
                    output.append(f"Free: {memory.get('free_mb')} MB")
                if memory.get("usage_percent") is not None:
                    output.append(f"Usage: {memory.get('usage_percent'):.1f}%")
                    
            # Disk information
            disk = data_content.get("disk", {})
            if disk:
                output.append("\nDisk Information:")
                if disk.get("total_gb") is not None:
                    output.append(f"Total: {disk.get('total_gb'):.1f} GB")
                if disk.get("used_gb") is not None:
                    output.append(f"Used: {disk.get('used_gb'):.1f} GB")
                if disk.get("free_gb") is not None:
                    output.append(f"Free: {disk.get('free_gb'):.1f} GB")
                if disk.get("usage_percent") is not None:
                    output.append(f"Usage: {disk.get('usage_percent'):.1f}%")
                
        elif data["type"] == "current_location" or data["type"] == "location" or data["type"] == "reverse_geocode":
            # Show location details
            loc_data = data_content
            if loc_data.get('name'):
                output.append(f"Name: {loc_data.get('name', 'Unknown')}")
            
            coords = loc_data.get("coordinates", {})
            if coords and coords.get("latitude") is not None and coords.get("longitude") is not None:
                output.append(f"Coordinates: {coords.get('latitude')}, {coords.get('longitude')}")
            
            address = loc_data.get("address", {})
            if address:
                address_parts = []
                if address.get("city"):
                    address_parts.append(f"City: {address['city']}")
                if address.get("region"):
                    address_parts.append(f"Region: {address['region']}")
                if address.get("country"):
                    address_parts.append(f"Country: {address['country']}")
                if address.get("zip"):
                    address_parts.append(f"Postal code: {address['zip']}")
                if address_parts:
                    output.extend(address_parts)
            
            # Show additional location metadata
            if loc_data.get("timezone"):
                output.append(f"Timezone: {loc_data.get('timezone')}")
            if loc_data.get("isp"):
                output.append(f"ISP: {loc_data.get('isp')}")
            if loc_data.get("as"):
                output.append(f"Network: {loc_data.get('as')}")
        
        # News types
        elif "news" in data["type"].lower():
            # Show news articles if available
            articles = data_content.get("articles", [])
            total = data_content.get("total_results", 0)
            
            # Get the number of articles to show from the parameters if available
            show_count = 5  # Default
            if "parameters" in data and "show" in data["parameters"]:
                show_count = data["parameters"]["show"]
            
            output.append(f"Total results: {total}")
            
            if articles:
                output.append(f"\nHeadlines:")
                for i, article in enumerate(articles[:show_count], 1):
                    output.append(f"\n{i}. {article.get('title', 'No title')}")
                    if article.get('description'):
                        output.append(f"   {article.get('description')[:100]}...")
                    if article.get('source') and article['source'].get('name'):
                        output.append(f"   Source: {article['source']['name']}")
                    if article.get('publishedAt'):
                        output.append(f"   Published: {article.get('publishedAt')}")
                    if article.get('url'):
                        output.append(f"   URL: {article.get('url')}")
                
                if len(articles) > show_count:
                    output.append(f"\n... and {len(articles) - show_count} more articles")
            else:
                # Show a message for empty results
                if "error" in data:
                    output.append("\nNo articles available. Please check the error message above.")
                else:
                    output.append("\nNo articles found for this query.")
    
    return "\n".join(output)


def time_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle time command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        Time data
    """
    return context.time.now(format_as_json=True, timezone=args.timezone)


def weather_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle weather command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        Weather data
    """
    # Use current location if none provided
    location = args.location if args.location else get_current_location(context)
    
    if args.all:
        return context.weather.get_complete_weather_data(location)
    elif args.detailed:
        return context.weather.get_detailed_weather(location)
    else:
        return context.weather.current(location)


def air_quality_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle air quality command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        Air quality data
    """
    # Use current location if none provided
    location = args.location if args.location else get_current_location(context)
    return context.weather.get_air_quality(location)


def astronomy_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle astronomy command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        Astronomy data
    """
    # Use current location if none provided
    location = args.location if args.location else get_current_location(context)
    return context.weather.get_astronomy(location)


def all_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle all command - get all contextual information.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        All context data
    """
    return context.get_all_context()


def system_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle system command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        System data
    """
    return context.system.get_system_info()


def user_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle user command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        User data
    """
    return context.system.get_user_info()


def who_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle who command - get information about users logged into the system.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        Logged users data
    """
    return context.system.get_logged_users()


def machine_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle machine command - get information about the local machine.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        Machine data
    """
    return context.system.get_machine_info()


def location_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle location command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        Location data
    """
    if args.query:
        return context.location.get(args.query)
    else:
        # Get current location if none provided
        try:
            return context.location.get_current_location()
        except Exception as e:
            # If automatic detection fails, return a generic error response
            return {
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "type": "location_error",
                "data": {
                    "error": str(e),
                    "message": "Could not detect current location automatically"
                }
            }


def news_command(args: argparse.Namespace, context: Contextuals) -> Dict[str, Any]:
    """Handle news command.
    
    Args:
        args: Command arguments
        context: Contextuals instance
        
    Returns:
        News data
    """
    try:
        result = None
        
        # Search query takes precedence over all other options
        if args.search:
            result = context.news.search_news(args.search, page_size=args.limit)
        
        # World news (--world flag)
        elif args.world:
            result = context.news.get_world_news(category=args.category, page_size=args.limit)
        
        # Explicit country specified (--country)
        elif args.country:
            # Ensure country code is always lowercase for consistency
            country_code = args.country.lower()
            result = context.news.get_country_news(country=country_code, category=args.category, page_size=args.limit)
        
        # No source specified - always use world news by default
        else:
            # Always use world news by default
            print("Showing world news by default.", file=sys.stderr)
            result = context.news.get_world_news(category=args.category, page_size=args.limit)
        
        # Add the show parameter to the result
        if result and "parameters" in result:
            result["parameters"]["show"] = args.show
        elif result:
            result["parameters"] = {"show": args.show}
        
        return result
        
    except Exception as e:
        # Handle missing API key or other errors
        error_message = str(e)
        if "MissingAPIKeyError" in error_message or "news" in error_message.lower() and "api key" in error_message.lower():
            print("Warning: News API key not found. Please set CONTEXTUALS_NEWS_API_KEY environment variable.", file=sys.stderr)
        else:
            print(f"Error retrieving news: {error_message}", file=sys.stderr)
            
        # Return a simple response with the error
        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "request_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "type": "news_error",
            "error": error_message,
            "parameters": {"show": args.show},
            "data": {
                "total_results": 0,
                "articles": []
            }
        }


def get_current_location(context: Contextuals) -> str:
    """Get current location using system IP address.
    
    Args:
        context: Contextuals instance
        
    Returns:
        Current location name or default location
    """
    try:
        # Try to get current location from IP
        current_location = context.location.get_current_location()
        
        # Extract location name
        if current_location and "data" in current_location:
            location_data = current_location["data"]
            if "name" in location_data and location_data["name"]:
                return location_data["name"]
            
            # If no name is available, try to construct from address components
            address = location_data.get("address", {})
            if address:
                location_parts = []
                if address.get("city"):
                    location_parts.append(address["city"])
                if address.get("region"):
                    location_parts.append(address["region"])
                if address.get("country"):
                    location_parts.append(address["country"])
                
                if location_parts:
                    return ", ".join(location_parts)
    except Exception as e:
        print(f"Warning: Could not determine current location: {e}", file=sys.stderr)
    
    # If we couldn't determine location, ask the user for it
    print("Could not automatically determine your location.", file=sys.stderr)
    print("Please specify a location (e.g. 'Paris, France'):", file=sys.stderr)
    try:
        user_location = input("> ")
        if user_location.strip():
            return user_location.strip()
    except (KeyboardInterrupt, EOFError):
        pass
    
    # As a last resort, default to a well-known location
    return "London"

def main() -> None:
    """Main entry point for CLI."""
    # Create main parser
    parser = argparse.ArgumentParser(description="Contextual information for AI applications")
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # All command - get all context information
    all_parser = subparsers.add_parser("all", help="Get all contextual information")
    all_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                          help="Output format (default: pretty)")
    
    # Time command
    time_parser = subparsers.add_parser("time", help="Get current time")
    time_parser.add_argument("--timezone", help="Timezone (e.g., 'America/New_York')")
    time_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                          help="Output format (default: pretty)")
    
    # Weather command
    weather_parser = subparsers.add_parser("weather", help="Get weather information")
    weather_parser.add_argument("location", nargs='?', help="Location to get weather for (omit to use current location)")
    weather_parser.add_argument("--detailed", action="store_true", help="Get detailed weather information")
    weather_parser.add_argument("--all", action="store_true", help="Get all weather information")
    weather_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                             help="Output format (default: pretty)")
    
    # Air quality command
    air_parser = subparsers.add_parser("air-quality", help="Get air quality information")
    air_parser.add_argument("location", nargs='?', help="Location to get air quality for (omit to use current location)")
    air_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                          help="Output format (default: pretty)")
    
    # Astronomy command
    astro_parser = subparsers.add_parser("astronomy", help="Get astronomy information")
    astro_parser.add_argument("location", nargs='?', help="Location to get astronomy data for (omit to use current location)")
    astro_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                           help="Output format (default: pretty)")
    
    # Location command
    location_parser = subparsers.add_parser("location", help="Get location information")
    location_parser.add_argument("query", nargs='?', help="Location to look up (omit to get current location)")
    location_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                              help="Output format (default: pretty)")
    
    # News command
    news_parser = subparsers.add_parser("news", help="Get news information")
    news_source = news_parser.add_mutually_exclusive_group()
    news_source.add_argument("--world", action="store_true", help="Get world news (international sources)")
    news_source.add_argument("--country", help="Country code (e.g., 'us', 'gb', 'fr', 'de', 'it', 'es', 'ru', 'cn', 'jp')")
    news_parser.add_argument("--category", choices=["business", "entertainment", "general", 
                                                  "health", "science", "sports", "technology"],
                           help="News category")
    news_parser.add_argument("--search", help="Search query")
    news_parser.add_argument("--limit", type=int, default=10, help="Number of articles to return")
    news_parser.add_argument("--show", type=int, default=5, 
                           help="Number of articles to display in pretty format (default: 5, ignored in JSON/compact format)")
    news_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                          help="Output format (default: pretty)")
        
    # User command
    user_parser = subparsers.add_parser("user", help="Get current user information")
    user_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                           help="Output format (default: pretty)")
                           
    # Who command
    who_parser = subparsers.add_parser("who", help="Get information about who is logged into the system")
    who_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                          help="Output format (default: pretty)")
                          
    # Machine command
    machine_parser = subparsers.add_parser("machine", help="Get information about the local machine")
    machine_parser.add_argument("--format", choices=["pretty", "json", "compact"], default="pretty",
                              help="Output format (default: pretty)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize Contextuals
    context = Contextuals()
    
    # Execute appropriate command
    try:
        if args.command == "all":
            result = all_command(args, context)
        elif args.command == "time":
            result = time_command(args, context)
        elif args.command == "weather":
            result = weather_command(args, context)
        elif args.command == "air-quality":
            result = air_quality_command(args, context)
        elif args.command == "astronomy":
            result = astronomy_command(args, context)
        elif args.command == "location":
            result = location_command(args, context)
        elif args.command == "news":
            result = news_command(args, context)
        elif args.command == "user":
            result = user_command(args, context)
        elif args.command == "who":
            result = who_command(args, context)
        elif args.command == "machine":
            result = machine_command(args, context)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
        # Print result
        # Get format from args (each subcommand has its own format argument)
        output_format = getattr(args, "format", "pretty")
        print(format_output(result, output_format))
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()