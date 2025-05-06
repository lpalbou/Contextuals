# Contextual-CC Command-Line Interface

Contextual-CC provides a convenient command-line interface (CLI) for quickly accessing contextual information without writing code.

## Installation

To install Contextual-CC with CLI support:

```bash
pip install "contextual-cc[cli]"
```

## Basic Usage

The basic syntax for the CLI is:

```bash
contextual [OPTIONS] COMMAND [ARGS]
```

### Global Options

- `--format FORMAT` - Output format (choices: pretty, json, compact; default: pretty)

### Available Commands

- `time` - Get current time information
- `weather` - Get weather information for a location
- `air-quality` - Get air quality information for a location
- `astronomy` - Get astronomy data (sunrise/sunset) for a location
- `location` - Get information about a location
- `news` - Get news headlines and articles

## Command Reference

### Time Command

Get current time information, optionally in a specific timezone.

```bash
contextual time [--timezone TIMEZONE]
```

Options:
- `--timezone TIMEZONE` - Timezone (e.g., 'America/New_York')

Examples:
```bash
# Get current time in local timezone
contextual time

# Get current time in Tokyo
contextual time --timezone Asia/Tokyo

# Get time as JSON
contextual time --format json
```

### Weather Command

Get weather information for a location.

```bash
contextual weather [LOCATION] [--detailed] [--all] [--format FORMAT]
```

Arguments:
- `LOCATION` - Optional location to get weather for (e.g., 'London', 'New York'). If omitted, uses your current location.

Options:
- `--detailed` - Get detailed weather information (UV, visibility, pressure)
- `--all` - Get complete weather report (current, forecast, air quality, astronomy)
- `--format FORMAT` - Output format (pretty, json, compact)

Examples:
```bash
# Get basic weather information for your current location
contextual weather

# Get basic weather information for London
contextual weather London

# Get detailed weather information for Paris
contextual weather Paris --detailed

# Get all weather information for Tokyo
contextual weather Tokyo --all

# Get weather as JSON
contextual weather London --format json
```

### Air Quality Command

Get air quality information for a location.

```bash
contextual air-quality [LOCATION] [--format FORMAT]
```

Arguments:
- `LOCATION` - Optional location to get air quality for. If omitted, uses your current location.

Options:
- `--format FORMAT` - Output format (pretty, json, compact)

Examples:
```bash
# Get air quality for your current location
contextual air-quality

# Get air quality for Beijing
contextual air-quality Beijing

# Get air quality as compact JSON
contextual air-quality London --format compact
```

### Astronomy Command

Get astronomy data (sunrise, sunset, moon phases) for a location.

```bash
contextual astronomy [LOCATION] [--format FORMAT]
```

Arguments:
- `LOCATION` - Optional location to get astronomy data for. If omitted, uses your current location.

Options:
- `--format FORMAT` - Output format (pretty, json, compact)

Examples:
```bash
# Get astronomy data for your current location
contextual astronomy

# Get astronomy data for Sydney
contextual astronomy Sydney

# Get astronomy data as JSON
contextual astronomy London --format json
```

### Location Command

Get information about a location.

```bash
contextual location [QUERY] [--format FORMAT]
```

Arguments:
- `QUERY` - Optional location name to look up. If omitted, returns your current location information.

Options:
- `--format FORMAT` - Output format (pretty, json, compact)

Examples:
```bash
# Get your current location information
contextual location

# Get information about the Eiffel Tower
contextual location "Eiffel Tower"

# Get location information as JSON
contextual location "Grand Canyon" --format json
```

### News Command

Get news headlines and articles.

```bash
contextual news [--world | --country COUNTRY] [--category CATEGORY] [--search SEARCH] [--limit LIMIT] [--show SHOW] [--format FORMAT]
```

Options:
- `--world` - Get world news from international sources
- `--country COUNTRY` - Country code (e.g., 'us', 'gb', 'fr', 'de', 'jp')
- `--category CATEGORY` - News category (choices: business, entertainment, general, health, science, sports, technology)
- `--search SEARCH` - Search query
- `--limit LIMIT` - Number of articles to retrieve (default: 10)
- `--show SHOW` - Number of articles to display in pretty format (default: 5)
- `--format FORMAT` - Output format (pretty, json, compact)

**Notes**:
- If no source option is provided, news for your current location (auto-detected) will be shown
- If auto-detection fails, world news will be shown as a fallback
- The `--search` option takes precedence over country/world options

**Country Codes**:
- `us` - United States
- `gb` - United Kingdom
- `fr` - France
- `de` - Germany
- `it` - Italy
- `es` - Spain
- `ru` - Russia
- `in` - India
- `cn` - China
- `jp` - Japan
- `au` - Australia
- `ca` - Canada
- `br` - Brazil

Examples:
```bash
# Get news for your current location (auto-detected)
contextual news

# Get world news
contextual news --world

# Get news for France
contextual news --country fr

# Get technology news for your current location
contextual news --category technology

# Get business news from Germany
contextual news --country de --category business

# Get news about climate change
contextual news --search "climate change"

# Show 10 articles in the results
contextual news --show 10

# Get 15 articles about AI in JSON format
contextual news --search "artificial intelligence" --limit 15 --format json
```


## Output Formats

The CLI supports three output formats:

1. `pretty` (default) - Human-readable formatted output
2. `json` - Formatted JSON with indentation
3. `compact` - Compact JSON without indentation

Example:
```bash
# Get weather in pretty format (default)
contextual weather London

# Get weather as formatted JSON
contextual weather London --format json

# Get weather as compact JSON (useful for piping to other tools)
contextual weather London --format compact
```

## Environment Variables

The CLI uses the same environment variables as the library:

- `CONTEXTUAL_CC_WEATHER_API_KEY` - OpenWeatherMap API key
- `CONTEXTUAL_CC_NEWS_API_KEY` - NewsAPI key

These can be set in your shell environment before running the CLI:

```bash
export CONTEXTUAL_CC_WEATHER_API_KEY="your_openweathermap_api_key"
export CONTEXTUAL_CC_NEWS_API_KEY="your_newsapi_key"
```

## Piping and Scripting

The CLI is designed to work well with other command-line tools:

```bash
# Pipe weather data to jq for filtering
contextual weather London --format json | jq '.data.temp_c'

# Use in a shell script
if [ $(contextual weather London --format compact | jq -r '.data.condition.text') == "Rain" ]; then
    echo "Remember to take an umbrella!"
fi
```

## Error Handling

When an error occurs, the CLI will print an error message to stderr and exit with a non-zero status code:

```bash
# Example of handling errors in a shell script
if ! contextual weather London; then
    echo "Could not get weather data, using default settings"
fi
```