# Contextuals Prompt Variants - Objective Testing Results

## Overview

We conducted comprehensive objective testing of 5 different prompt variants using **Qwen 3 30B** via Ollama to determine which provides the best contextual awareness for LLM applications.

## Test Methodology

### Test Setup
- **Model**: Qwen 3 30B (qwen3:30b-a3b-q4_K_M)
- **Framework**: PydanticAI with Ollama
- **Questions**: 10 diverse contextual awareness scenarios
- **Metrics**: Contextual awareness score, token efficiency, response time, context coverage

### Test Questions
1. Weather-based clothing recommendation
2. Health and safety assessment for outdoor activity  
3. Cultural and linguistic appropriateness
4. System performance diagnosis
5. Time zone and scheduling awareness
6. Environmental health decision
7. Current events awareness
8. Multi-factor activity planning
9. Personalized productivity optimization
10. Transportation decision with multiple factors

## Results Summary

### Final Rankings

| Rank | Variant    | Score | Coverage | Tokens | Efficiency* | Avg Time |
|------|------------|-------|----------|--------|-------------|----------|
| 1    | DEFAULT    | 0.980 | 1.000    | 126    | 0.778       | 14.6s    |
| 2    | STRUCTURED | 0.980 | 1.000    | 53     | 1.849       | 13.5s    |
| 3    | COMPACT    | 0.960 | 1.000    | 28     | 3.429       | 17.3s    |
| 4    | MINIMAL    | 0.930 | 1.000    | 20     | 4.650       | 13.6s    |
| 5    | DETAILED   | 0.910 | 0.929    | 219    | 0.416       | 16.8s    |

*Efficiency = Score per 100 tokens

## Key Findings

### 1. **STRUCTURED** Variant - Best Overall Choice
- **Score**: 0.980 (tied for highest)
- **Token Efficiency**: 1.849 (2nd highest)
- **Tokens**: 53 (moderate)
- **Strengths**: Excellent balance of awareness and efficiency, parseable format
- **Use Case**: **Recommended for most production applications**

### 2. **DEFAULT** Variant - Highest Awareness
- **Score**: 0.980 (tied for highest)
- **Token Efficiency**: 0.778 (moderate)
- **Tokens**: 126 (higher)
- **Strengths**: Best overall contextual awareness, comprehensive coverage
- **Use Case**: Standard applications without strict token limits

### 3. **COMPACT** Variant - Production Balance
- **Score**: 0.960 (very high)
- **Token Efficiency**: 3.429 (high)
- **Tokens**: 28 (low)
- **Strengths**: Good balance of efficiency and awareness
- **Use Case**: Production environments with moderate token constraints

### 4. **MINIMAL** Variant - Maximum Efficiency
- **Score**: 0.930 (good)
- **Token Efficiency**: 4.650 (highest)
- **Tokens**: 20 (lowest)
- **Strengths**: Ultra-efficient, essential context only
- **Use Case**: Extreme token limits, mobile apps, embedded systems

### 5. **DETAILED** Variant - Comprehensive Context
- **Score**: 0.910 (lowest)
- **Token Efficiency**: 0.416 (lowest)
- **Tokens**: 219 (highest)
- **Strengths**: Rich context, detailed guidelines
- **Use Case**: Complex scenarios requiring extensive context

## Surprising Results

1. **DETAILED variant performed worst** despite having the most information
   - Likely due to information overload confusing the model
   - Lower context coverage (0.929 vs 1.000 for others)

2. **STRUCTURED variant tied for best score** with much fewer tokens than DEFAULT
   - JSON-like format appears to help model parse context efficiently
   - Best token efficiency among high-scoring variants

3. **MINIMAL variant achieved 0.930 score** with only 20 tokens
   - Demonstrates that concise, well-structured context can be highly effective
   - Highest token efficiency overall

## Recommendations by Use Case

### Production Applications (General)
**Use: STRUCTURED variant**
- Excellent contextual awareness (0.980)
- High token efficiency (1.849)
- Parseable format for programmatic use

### Token-Constrained Environments
**Use: COMPACT or MINIMAL variants**
- COMPACT: Better awareness (0.960) with 28 tokens
- MINIMAL: Maximum efficiency (4.650) with 20 tokens

### Rich Context Requirements
**Use: DEFAULT variant**
- Highest contextual awareness (0.980)
- Comprehensive coverage (1.000)
- Clear, readable format

### API Integrations
**Use: STRUCTURED variant**
- JSON-like format easy to parse
- Excellent performance
- Moderate token usage

## Prompt Variant Contents

### DEFAULT Prompt (126 tokens)
```
CONTEXT: Real-time user environment data for personalized responses.
TIME: 2025-05-26T18:55:12.406666+00:00
USER: albou (Laurent-Philippe Albou) | Lang: en_US.UTF-8
LOCATION: Paris, France (48.86,2.35)
WEATHER: 17.45°C, clear sky, 54% humidity, 16.668km/h WSW
AIR: AQI 2 (Fair) - Enjoy your usual outdoor activities.
SUN: Rise 05:56:35, Set 21:39:04 | Moon: New Moon
SYSTEM: macOS-15.3.1-arm64-arm-64bit, Apple M4 Max, 12GB free
NEWS: Senators eye more budget bill cuts, despite House ... | Fed Chair Powell praises integrity and public serv...

USAGE: Reference this context for location-aware, time-sensitive, weather-appropriate, and culturally relevant responses. Consider user's environment, current conditions, and local context in your assistance.
```

### STRUCTURED Prompt (53 tokens) - **RECOMMENDED**
```
CONTEXT_DATA: {
  "user": "albou (Laurent-Philippe Albou)",
  "location": "unknown, unknown",
  "time": "2025-05-26T18:55",
  "weather": "17.45°C, clear sky",
  "air_quality": "AQI 2 (Fair)",
  "system": "macOS-15.3.1-arm64-arm-64bit"
}

INSTRUCTIONS: Use this context to provide location-aware, time-sensitive, weather-appropriate responses. Consider user's environment and local conditions in all assistance.
```

### COMPACT Prompt (28 tokens)
```
CTX: 2025-05-26T18:55 | USR: albou | unknown,unknown | ENV: 17.45°C clear sky | AQI:2 | SYS: macOS-15.3.1-ar | Use for location/time/weather-aware responses.
```

### MINIMAL Prompt (20 tokens)
```
User: albou in unknown, unknown | 17.45°C clear sky | 2025-05-26T18:55 | Personalize responses to location/weather/time.
```

### DETAILED Prompt (219 tokens)
```
=== CONTEXTUAL INFORMATION ===
This data provides real-time user environment context for personalized assistance.

TEMPORAL CONTEXT:
• Current time: 2025-05-26T18:55:15.428597+00:00

USER PROFILE:
• Name: Laurent-Philippe Albou (albou)
• Language/Locale: en_US.UTF-8

GEOGRAPHIC CONTEXT:
• Location: unknown, unknown
• Coordinates: 0.0000, 0.0000

ENVIRONMENTAL CONDITIONS:
• Weather: 17.45°C, clear sky
• Wind: 16.668 km/h WSW, Humidity: 54%
• Air Quality: Fair (AQI 2)
• Health Advice: Enjoy your usual outdoor activities.

ASTRONOMICAL DATA:
• Sunrise: 05:56:35, Sunset: 21:39:04
• Moon Phase: New Moon

CURRENT NEWS CONTEXT:
• Senators eye more budget bill cuts, despite House speaker's plea for few changes (The Washington Post)
• Fed Chair Powell praises integrity and public service amid unrelenting Trump attacks (CNN)
• Brent fire: Names of four people who died released by police (BBC News)

USAGE GUIDELINES:
• Reference location for local recommendations, services, and cultural context
• Consider weather for activity suggestions and safety advice
• Use time context for scheduling and time-sensitive information
• Adapt language and cultural references to user's locale
• Factor in air quality for health-related recommendations
```

## Implementation

All variants are available in the Contextuals library:

```python
from contextuals import Contextuals

context = Contextuals()

# Recommended for most use cases
structured_prompt = context.get_context_prompt_structured()

# Other variants
default_prompt = context.get_context_prompt()
compact_prompt = context.get_context_prompt_compact()
minimal_prompt = context.get_context_prompt_minimal()
detailed_prompt = context.get_context_prompt_detailed()
```

## CLI Usage

```bash
# Default variant
contextuals prompt

# Specific variants
contextuals prompt --variant structured  # Recommended
contextuals prompt --variant compact     # Efficient
contextuals prompt --variant minimal     # Ultra-efficient
contextuals prompt --variant detailed    # Comprehensive
```

## Conclusion

The objective testing with Qwen 3 30B provides clear empirical evidence that:

1. **STRUCTURED variant is the best choice for most applications** - combining excellent contextual awareness with high token efficiency
2. **More tokens don't always mean better performance** - the DETAILED variant performed worst despite having the most information
3. **Well-structured, concise context is highly effective** - even the MINIMAL variant achieved 93% contextual awareness
4. **Token efficiency varies dramatically** - from 0.416 to 4.650 score per 100 tokens

This testing methodology provides a replicable framework for evaluating contextual prompt effectiveness with real LLMs. 