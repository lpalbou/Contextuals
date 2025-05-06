"""Example of AI integration with Contextual-CC."""

import os
from contextual_cc import ContextualCC

def main():
    """Demonstrate how to integrate contextual information with AI models."""
    print("=== AI Integration Example ===\n")
    
    # Initialize context provider
    context = ContextualCC()
    
    try:
        # Get enriched context
        time_info = context.time.now(format_as_json=True)
        location_name = "London"
        
        # Get weather if available
        weather_text = "Weather information not available"
        if os.environ.get("CONTEXTUAL_CC_WEATHER_API_KEY"):
            try:
                weather = context.weather.current(location_name)
                weather_text = f"{weather['data']['temp_c']}°C, {weather['data']['condition']['text']}"
            except Exception:
                pass
        
        # Get news if available
        news_text = "News information not available"
        if os.environ.get("CONTEXTUAL_CC_NEWS_API_KEY"):
            try:
                news = context.news.get_top_headlines(country="gb", page_size=2)
                news_text = "\n".join([f"- {a['title']}" for a in news["data"]["articles"][:2]])
            except Exception:
                pass
        
        # Get system information
        system_info = context.system.get_system_info()
        system_text = (f"OS: {system_info['data']['os']['system']} "
                       f"{system_info['data']['os']['release']}")
        user_info = context.system.get_user_info()
        user_text = f"User: {user_info['data']['username']}"
        
        # Create context-aware prompt
        prompt = f"""
Current time: {time_info['data']['datetime']}
Current weather in {location_name}: {weather_text}
{system_text}
{user_text}
Top headlines:
{news_text}

Given this context, please provide a personalized greeting and suggestion for the user's day.
"""

        print("AI Prompt with Contextual Information:")
        print(prompt)
        
        # In a real application, you would send this to your AI model
        print("\nIn a real application, this prompt would be sent to an AI model.")
        print("Example code for sending to OpenAI:")
        print("""
import openai

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
)

print(response.choices[0].message.content)
""")

        # Example for Anthropic Claude
        print("\nExample code for sending to Anthropic Claude:")
        print("""
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20240229",
    system="You are a helpful assistant.",
    max_tokens=1000,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print(response.content[0].text)
""")
    
    except Exception as e:
        print(f"AI integration example failed: {e}")


if __name__ == "__main__":
    main()