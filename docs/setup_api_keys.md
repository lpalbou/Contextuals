# Setting Up API Keys

This guide explains how to obtain and set up API keys for the various services used by Contextuals.

## Table of Contents
- [Weather API](#weather-api)
- [News API](#news-api)
- [Location API](#location-api)
- [Setting API Keys in Your Environment](#setting-api-keys-in-your-environment)
- [Setting API Keys in Your Code](#setting-api-keys-in-your-code)

## Weather API

Contextuals uses [OpenWeatherMap.org](https://openweathermap.org/) for weather information by default.

### Getting an OpenWeatherMap API Key

1. Go to [OpenWeatherMap.org](https://openweathermap.org/)
2. Sign up for a free account
3. After signing up and logging in, go to the "API keys" tab in your account
4. Your API key will be displayed on this page
5. The free tier provides access to current weather, 5-day forecast, and air quality
6. Note that your API key may take a few hours to become active after registration

## News API

Contextuals uses [NewsAPI.org](https://newsapi.org/) to retrieve news headlines and articles.

### Getting a NewsAPI.org API Key

1. Go to [NewsAPI.org](https://newsapi.org/)
2. Sign up for a free account
3. After signing up and logging in, your API key will be displayed on the dashboard
4. The free tier allows up to 100 requests per day, with a rate limit of 1 request per second
5. News headlines for the past month are available with the free tier

## Location API

For location services, Contextuals uses [OpenStreetMap's Nominatim API](https://nominatim.org/) by default. This service doesn't require an API key but has usage limitations:

- Maximum of 1 request per second
- No more than 25,000 requests per day
- Must include a valid User-Agent header (Contextuals handles this automatically)

For higher volume applications, you may want to use a different geocoding service and configure Contextuals accordingly.

## Setting API Keys in Your Environment

The recommended way to set API keys is through environment variables. This keeps your keys out of your source code.

### Linux/macOS

Add these lines to your `~/.bashrc`, `~/.zshrc`, or equivalent shell configuration file:

```bash
export CONTEXTUALS_WEATHER_API_KEY="your_weather_api_key"
export CONTEXTUALS_NEWS_API_KEY="your_news_api_key"
# Note: The default location provider (OpenStreetMap Nominatim) doesn't require an API key
```

Then reload your shell configuration:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Windows (Command Prompt)

Set environment variables in Command Prompt:

```cmd
set CONTEXTUALS_WEATHER_API_KEY=your_weather_api_key
set CONTEXTUALS_NEWS_API_KEY=your_news_api_key
REM Note: The default location provider (OpenStreetMap Nominatim) doesn't require an API key
```

To set them permanently, use the System Properties:
1. Right-click on "This PC" or "Computer" and select "Properties"
2. Click on "Advanced system settings"
3. Click on "Environment Variables"
4. Under "User variables", click "New" and add the variables

### Windows (PowerShell)

Set environment variables in PowerShell:

```powershell
$env:CONTEXTUALS_WEATHER_API_KEY = "your_weather_api_key"
$env:CONTEXTUALS_NEWS_API_KEY = "your_news_api_key"
# Note: The default location provider (OpenStreetMap Nominatim) doesn't require an API key
```

To make these permanent, add them to your PowerShell profile:
1. Create or edit your profile: `notepad $PROFILE`
2. Add the lines above
3. Save and restart PowerShell

## Setting API Keys in Your Code

You can also set API keys directly in your code, though this is less secure for production applications.

### Setting Keys During Initialization

```python
from contextuals import Contextuals

context = Contextuals(
    weather_api_key="your_weather_api_key",
    news_api_key="your_news_api_key"
    # Note: The default location provider (OpenStreetMap Nominatim) doesn't require an API key
)
```

### Setting Keys After Initialization

```python
from contextuals import Contextuals

context = Contextuals()
context.set_api_key("weather", "your_weather_api_key")
context.set_api_key("news", "your_news_api_key")
# Note: The default location provider (OpenStreetMap Nominatim) doesn't require an API key
```

## Using a .env File

For development, you can use a `.env` file with the [python-dotenv](https://pypi.org/project/python-dotenv/) package, which Contextuals includes as a dependency.

1. Create a file named `.env` in your project root:
   ```
   CONTEXTUALS_WEATHER_API_KEY=your_weather_api_key
   CONTEXTUALS_NEWS_API_KEY=your_news_api_key
   # Note: The default location provider (OpenStreetMap Nominatim) doesn't require an API key
   ```

2. The environment variables will be loaded automatically when you import Contextuals.

**Important:** Don't commit `.env` files to source control. Add them to your `.gitignore` file:
```
# .gitignore
.env
```