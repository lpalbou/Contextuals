"""Utility functions for news module."""

from typing import Dict, Any, List, Optional
import datetime


def format_date(date_str: str) -> str:
    """Format a date string to a standardized format.
    
    Args:
        date_str: Date string in various formats.
        
    Returns:
        Formatted date string (YYYY-MM-DD).
    """
    try:
        # Parse various date formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601
            "%Y-%m-%d %H:%M:%S",    # Standard format
            "%Y-%m-%d",             # Date only
            "%d/%m/%Y",             # DD/MM/YYYY
            "%m/%d/%Y",             # MM/DD/YYYY
            "%B %d, %Y",            # Month name, day, year
        ]
        
        parsed_date = None
        for fmt in formats:
            try:
                parsed_date = datetime.datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if parsed_date:
            return parsed_date.strftime("%Y-%m-%d")
        
        # If we couldn't parse the date, return as is
        return date_str
    except Exception:
        # If any error occurs, return as is
        return date_str


def categorize_news(article: Dict[str, Any]) -> List[str]:
    """Categorize a news article based on its content.
    
    Args:
        article: News article data.
        
    Returns:
        List of categories for the article.
    """
    # This is a simple implementation based on keyword matching
    # In a real implementation, you would use a more sophisticated approach
    # like topic modeling or classification
    
    categories = []
    keywords = {
        "politics": ["government", "president", "minister", "election", "vote", "parliament", "congress", "senate", "political", "policy", "bill", "law"],
        "business": ["company", "market", "stock", "economy", "economic", "finance", "trade", "investment", "investor", "profit", "revenue", "bank"],
        "technology": ["tech", "technology", "ai", "artificial intelligence", "software", "hardware", "app", "computer", "internet", "digital", "cyber", "robot"],
        "science": ["science", "scientist", "research", "study", "discover", "experiment", "lab", "space", "physics", "chemistry", "biology", "medicine"],
        "health": ["health", "medical", "doctor", "hospital", "disease", "virus", "pandemic", "vaccine", "treatment", "diet", "drug", "medication"],
        "sports": ["sport", "team", "player", "game", "match", "tournament", "championship", "olympic", "score", "win", "lose", "football", "soccer", "baseball", "basketball", "tennis"],
        "entertainment": ["movie", "film", "tv", "television", "show", "star", "celebrity", "actor", "actress", "music", "artist", "album", "song", "concert"],
        "travel": ["travel", "tourism", "tourist", "vacation", "holiday", "hotel", "flight", "airline", "beach", "resort", "tour", "trip"],
    }
    
    # Check title and description for keywords
    text = ""
    if article.get("title"):
        text += article["title"].lower() + " "
    if article.get("description"):
        text += article["description"].lower() + " "
    if article.get("content"):
        text += article["content"].lower()
    
    # Match keywords
    for category, keyword_list in keywords.items():
        for keyword in keyword_list:
            if keyword in text:
                categories.append(category)
                break
    
    return categories or ["general"]


def summarize_article(article: Dict[str, Any], max_length: int = 200) -> str:
    """Generate a summary for a news article.
    
    Args:
        article: News article data.
        max_length: Maximum summary length.
        
    Returns:
        Article summary.
    """
    # If the article has a description, use that as the summary
    if article.get("description"):
        summary = article["description"]
        
        # Truncate if necessary
        if len(summary) > max_length:
            # Try to truncate at a sentence boundary
            sentence_ends = [i for i, char in enumerate(summary[:max_length]) if char in ['.', '!', '?']]
            if sentence_ends:
                # Truncate at the last sentence boundary
                summary = summary[:sentence_ends[-1] + 1]
            else:
                # If no sentence boundary, truncate at a word boundary
                summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
        
        return summary
    
    # If no description, use the content (truncated)
    if article.get("content"):
        content = article["content"]
        # Remove [+N chars] that sometimes appears at the end of content
        import re
        content = re.sub(r'\s*\[\+\d+ chars\]$', '', content)
        
        # Truncate if necessary
        if len(content) > max_length:
            # Try to truncate at a sentence boundary
            sentence_ends = [i for i, char in enumerate(content[:max_length]) if char in ['.', '!', '?']]
            if sentence_ends:
                # Truncate at the last sentence boundary
                content = content[:sentence_ends[-1] + 1]
            else:
                # If no sentence boundary, truncate at a word boundary
                content = content[:max_length].rsplit(' ', 1)[0] + '...'
        
        return content
    
    # If no description or content, use the title
    if article.get("title"):
        return article["title"]
    
    return "No summary available"


def get_news_sentiment(text: str) -> Dict[str, Any]:
    """Analyze the sentiment of a news article or text.
    
    Args:
        text: The text to analyze.
        
    Returns:
        Dictionary with sentiment information.
    """
    # This is a very simplistic sentiment analysis
    # In a real implementation, you would use a proper NLP library or API
    
    # List of positive and negative words
    positive_words = [
        "good", "great", "excellent", "positive", "success", "successful", "win", "winning",
        "happy", "glad", "pleased", "impressive", "impressive", "encourage", "encouraging",
        "hope", "hopeful", "confident", "innovative", "progress", "breakthrough", "advance"
    ]
    
    negative_words = [
        "bad", "terrible", "poor", "negative", "fail", "failure", "lose", "losing",
        "sad", "sorry", "unfortunate", "disappoint", "disappointing", "worry", "worrying",
        "fear", "fearful", "concern", "concerning", "decline", "crisis", "problem", "issue"
    ]
    
    # Count positive and negative words
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total = positive_count + negative_count
    if total == 0:
        score = 0  # Neutral
    else:
        score = (positive_count - negative_count) / total
        
    # Determine sentiment category
    if score > 0.25:
        sentiment = "positive"
    elif score < -0.25:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "score": score,  # -1.0 to 1.0, where -1.0 is very negative and 1.0 is very positive
        "positive_count": positive_count,
        "negative_count": negative_count,
    }