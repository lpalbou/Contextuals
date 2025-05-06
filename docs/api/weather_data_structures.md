# Weather API Data Structures

This document describes the data structures returned by the various weather API methods in Contextuals.

## Common Structure

All weather-related responses follow this common structure:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",    // When the data was retrieved
  "request_time": "2023-05-15T12:34:56.789012+00:00", // When the request was made
  "type": "current_weather",                          // The type of data
  "is_cached": false,                                 // Whether this data came from cache
  "location": {                                       // Location information
    "name": "London",
    "country": "GB",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {                                           // The actual weather data
    // Data specific to the request type
  }
}
```

## Current Weather

Returned by `context.weather.current(location)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "current_weather",
  "is_cached": false,
  "location": {
    "name": "London",
    "country": "GB",
    "lat": 51.51,
    "lon": -0.13,
    "localtime": "2023-05-15T13:34:56"
  },
  "data": {
    "temp_c": 15.5,                      // Temperature in Celsius
    "temp_f": 59.9,                      // Temperature in Fahrenheit
    "is_day": 1,                         // 1 if daytime, 0 if nighttime
    "condition": {                       // Weather condition
      "text": "Partly cloudy",           // Human-readable description
      "code": 802                        // Condition code
    },
    "wind_mph": 8.1,                     // Wind speed in miles per hour
    "wind_kph": 13.0,                    // Wind speed in kilometers per hour
    "wind_degree": 270,                  // Wind direction in degrees
    "wind_dir": "W",                     // Wind direction as compass point
    "humidity": 76,                      // Relative humidity percentage
    "cloud": 25,                         // Cloud cover percentage
    "feelslike_c": 14.2,                 // Feels like temperature in Celsius
    "feelslike_f": 57.6,                 // Feels like temperature in Fahrenheit
    "pressure": 1012,                    // Atmospheric pressure in hPa
    "visibility": 10000                  // Visibility in meters
  }
}
```

## Air Quality

Returned by `context.weather.get_air_quality(location)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "air_quality",
  "is_cached": false,
  "location": {
    "name": "London",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "pollutants": {
      "co": 250.0,                      // Carbon monoxide (μg/m3)
      "o3": 70.0,                       // Ozone (μg/m3)
      "no2": 15.0,                      // Nitrogen dioxide (μg/m3)
      "so2": 5.0,                       // Sulphur dioxide (μg/m3)
      "pm2_5": 4.0,                     // Fine particles (μg/m3)
      "pm10": 10.0,                     // Coarse particles (μg/m3)
      "nh3": 2.0                        // Ammonia (μg/m3)
    },
    "aqi": {
      "value": 2,                       // Air Quality Index (1-5)
      "description": "Fair",            // Human-readable AQI description
      "health_implications": "Air quality is acceptable; however, some pollutants may be a concern for a very small number of people who are unusually sensitive to air pollution."
    },
    "health_context": {
      "pm2_5": {                         // Health context for each pollutant
        "value": 4.0,
        "unit": "μg/m3",
        "who_guideline": 5,
        "status": "Below WHO guideline",
        "health_risk": "Low"
      },
      "pm10": {
        "value": 10.0,
        "unit": "μg/m3",
        "who_guideline": 15,
        "status": "Below WHO guideline",
        "health_risk": "Low"
      },
      // ... Other pollutants
    },
    "recommendations": {
      "general": "Enjoy your usual outdoor activities.",
      "sensitive_groups": "Consider reducing intense outdoor activities if you experience symptoms.",
      "outdoor_activity": "Good conditions for most outdoor activities.",
      "ventilation": "Good time for home ventilation."
    }
  }
}
```

## Astronomy Data

Returned by `context.weather.get_astronomy(location)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "astronomy",
  "is_cached": false,
  "location": {
    "name": "London",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "sun": {
      "sunrise": "05:12:34",              // Sunrise time (HH:MM:SS)
      "sunset": "20:45:12",               // Sunset time (HH:MM:SS)
      "day_length": "15:32",              // Day length (HH:MM)
      "civil_twilight": {                 // Civil twilight (dawn/dusk)
        "begin": "04:42:34",              // Morning twilight begins
        "end": "21:15:12"                 // Evening twilight ends
      }
    },
    "moon": {
      "moonrise": "19:23:45",             // Moonrise time (HH:MM:SS)
      "moonset": "04:56:12",              // Moonset time (HH:MM:SS)
      "phase": 0.62,                      // Moon phase (0-1)
      "phase_description": "Waning Gibbous", // Human-readable phase description
      "illumination": 76                  // Moon illumination percentage
    }
  }
}
```

## Detailed Weather

Returned by `context.weather.get_detailed_weather(location)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "detailed_weather",
  "is_cached": false,
  "location": {
    "name": "London",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "uv_index": {
      "value": 4.2,                       // UV Index value
      "category": "Moderate",             // Category (Low, Moderate, High, Very High, Extreme)
      "risk_level": "Moderate risk of harm from unprotected sun exposure",
      "protection_required": "Wear sunglasses and use SPF 30+ sunscreen, cover the body with clothing and a hat, seek shade around midday."
    },
    "visibility": {
      "meters": 10000,                    // Visibility in meters
      "kilometers": 10.0,                 // Visibility in kilometers
      "description": "Very clear"         // Human-readable description
    },
    "pressure": {
      "value": 1012,                      // Pressure in hPa
      "unit": "hPa",
      "description": "Normal / Average"   // Human-readable description
    },
    "humidity": {
      "value": 76,                        // Humidity percentage
      "unit": "%",
      "comfort_level": "Slightly humid - may feel sticky"
    },
    "dew_point": {
      "value": 11.2,                      // Dew point in °C
      "unit": "°C",
      "description": "Comfortable - dry air"
    }
  }
}
```

## 24-Hour Forecast

Returned by `context.weather.get_forecast_24h(location)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "forecast_24h",
  "is_cached": false,
  "location": {
    "name": "London",
    "country": "GB",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "hours": [
      {
        "time": "2023-05-15 13:00",       // Hour timestamp
        "temp_c": 15.5,                   // Temperature in Celsius
        "temp_f": 59.9,                   // Temperature in Fahrenheit
        "condition": {
          "text": "Partly cloudy",
          "code": 802
        },
        "wind_mph": 8.1,
        "wind_kph": 13.0,
        "wind_degree": 270,
        "wind_dir": "W",
        "humidity": 76,
        "cloud": 25,
        "feelslike_c": 14.2,
        "feelslike_f": 57.6,
        "chance_of_rain": 10,             // Probability of rain (%)
        "chance_of_snow": 0,              // Probability of snow (%)
        "will_it_rain": 0,                // 1 if rain expected, 0 if not
        "will_it_snow": 0,                // 1 if snow expected, 0 if not
        "pressure": 1012,
        "visibility": 10000
      },
      // ... Data for 23 more hours
    ]
  }
}
```

## 7-Day Forecast

Returned by `context.weather.get_forecast_7day(location)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "forecast_7day",
  "is_cached": false,
  "location": {
    "name": "London",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "days": [
      {
        "date": "2023-05-15",             // Day date
        "max_temp_c": 17.2,               // Maximum temperature in Celsius
        "min_temp_c": 10.5,               // Minimum temperature in Celsius
        "avg_temp_c": 14.1,               // Average temperature in Celsius
        "max_temp_f": 63.0,               // Maximum temperature in Fahrenheit
        "min_temp_f": 50.9,               // Minimum temperature in Fahrenheit
        "avg_temp_f": 57.4,               // Average temperature in Fahrenheit
        "condition": {
          "text": "Partly cloudy",
          "code": 802
        },
        "uv": 4.2,                        // UV Index
        "chance_of_rain": 20,             // Probability of rain (%)
        "chance_of_snow": 0,              // Probability of snow (%)
        "totalprecip_mm": 1.2,            // Total precipitation in mm
        "totalprecip_in": 0.05,           // Total precipitation in inches
        "avghumidity": 76,                // Average humidity (%)
        "daily_will_it_rain": 0,          // 1 if rain expected, 0 if not
        "daily_will_it_snow": 0           // 1 if snow expected, 0 if not
      },
      // ... Data for 6 more days (or 4 more days on free tier)
    ]
  }
}
```

## Moon Phases

Returned by `context.weather.get_moon_phases(location, days=7)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "moon_phases",
  "is_cached": false,
  "location": {
    "name": "London",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "phases": [
      {
        "date": "2023-05-15",             // Date
        "moon_phase": "Waning Gibbous",   // Moon phase description
        "moon_illumination": "76",        // Moon illumination percentage
        "moonrise": "19:23",              // Moonrise time (HH:MM)
        "moonset": "04:56",               // Moonset time (HH:MM)
        "sunrise": "05:12",               // Sunrise time (HH:MM)
        "sunset": "20:45"                 // Sunset time (HH:MM)
      },
      // ... Data for 6 more days
    ]
  }
}
```

## Outdoor Activity Recommendation

Returned by `context.weather.get_outdoor_activity_recommendation(weather_data)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "type": "outdoor_recommendation",
  "recommendation": "Good weather conditions for outdoor activities.",
  "suitable_activities": [
    "all outdoor activities",
    "picnics",
    "hiking",
    "sports",
    "gardening"
  ],
  "weather_snapshot": {
    "condition": "Partly cloudy",
    "temperature_c": 15.5,
    "is_day": 1,
    "humidity": 76,
    "wind_kph": 13.0
  }
}
```

## Complete Weather Data

Returned by `context.weather.get_complete_weather_data(location)`:

```json
{
  "timestamp": "2023-05-15T12:34:56.789012+00:00",
  "request_time": "2023-05-15T12:34:56.789012+00:00",
  "type": "complete_weather_report",
  "is_cached": false,
  "location": {
    "name": "London",
    "country": "GB",
    "lat": 51.51,
    "lon": -0.13
  },
  "data": {
    "current": {
      // Current weather data (same structure as current weather response)
    },
    "air_quality": {
      // Air quality data (same structure as air quality response)
    },
    "detailed": {
      // Detailed weather data (same structure as detailed weather response)
    },
    "astronomy": {
      // Astronomy data (same structure as astronomy response)
    },
    "forecast_24h": {
      // 24-hour forecast data (same structure as 24h forecast response)
    },
    "forecast_7day": {
      // 7-day forecast data (same structure as 7-day forecast response)
    },
    "moon_phases": [
      // Moon phase data for next 7 days (same structure as moon phases response)
    ],
    "recommendation": {
      // Activity recommendation (same structure as recommendation response)
    }
  }
}
```