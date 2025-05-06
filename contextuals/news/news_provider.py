"""News provider for Contextuals."""

import datetime
import json
from typing import Dict, Any, Optional, List, Union
import requests

from contextuals.core.cache import Cache, cached
from contextuals.core.config import Config
from contextuals.core.exceptions import APIError, NetworkError, MissingAPIKeyError


class NewsProvider:
    """Provides news-related contextual information.
    
    Features:
    - Retrieves news from various sources
    - Filters news by country, category, or topic
    - Caches results to minimize API calls
    - Provides fallback data when offline
    - Returns structured JSON responses with timestamps
    - Uses location awareness for country-specific news
    """
    
    def __init__(self, config: Config, cache: Cache, context_manager=None):
        """Initialize the news provider.
        
        Args:
            config: Configuration instance.
            cache: Cache instance.
            context_manager: Optional context manager instance.
        """
        self.config = config
        self.cache = cache
        self.context_manager = context_manager
    
    def _get_api_key(self) -> str:
        """Get the news API key from configuration.
        
        Returns:
            API key as a string.
            
        Raises:
            MissingAPIKeyError: If API key is not found.
        """
        api_key = self.config.get_api_key("news")
        if not api_key:
            raise MissingAPIKeyError("news")
        return api_key
    
    def _get_current_date(self) -> str:
        """Get the current date in ISO format.
        
        This is used to indicate when the data was retrieved.
        
        Returns:
            Current date as string in ISO format.
        """
        if self.context_manager:
            return self.context_manager.get_current_datetime_iso()
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    def _get_current_country(self) -> Optional[str]:
        """Get the current country from the context manager.
        
        If not available, a default country may be used based on configuration.
        
        Returns:
            Country code (ISO alpha-2) or None if not available.
        """
        # Try to get country from context manager
        if self.context_manager:
            location = self.context_manager.get_current_location()
            if location and "address" in location and location["address"].get("country_code"):
                return location["address"]["country_code"].lower()
        
        # Fallback to default from config
        return self.config.get("default_country", "us")
    
    @cached(ttl=1800)  # Cache for 30 minutes
    def get_top_headlines(self, country: Optional[str] = None, category: Optional[str] = None, 
                         query: Optional[str] = None, page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Get top news headlines.
        
        If country is not specified, uses the current country from location context.
        
        Args:
            country: Country code (ISO alpha-2) for country-specific news.
            category: Category of news (e.g., business, technology, sports).
            query: Keywords or phrases to search for.
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with news headline information.
            
        Raises:
            NetworkError: If API request fails and no fallback is available.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        
        # Get country from context if not provided
        if country is None:
            country = self._get_current_country()
        
        # Ensure country code is lowercase
        if country:
            country = country.lower()
        
        # Create cache key based on parameters
        cache_key_parts = ["headlines"]
        if country:
            cache_key_parts.append(f"country:{country}")
        if category:
            cache_key_parts.append(f"category:{category}")
        if query:
            cache_key_parts.append(f"q:{query}")
        cache_key_parts.append(f"page:{page}")
        cache_key_parts.append(f"pageSize:{page_size}")
        cache_key = "_".join(cache_key_parts)
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            # Update timestamps but keep is_cached flag
            result = cached_data.copy()
            result["timestamp"] = response_time
            result["is_cached"] = True
            return result
        
        # If not in cache, fetch from API
        try:
            api_key = self._get_api_key()
            api_url = self.config.get("news_api_url", "https://newsapi.org/v2/top-headlines")
            
            params = {
                "apiKey": api_key,
                "pageSize": min(100, max(1, page_size)),  # Ensure it's between 1 and 100
                "page": max(1, page),  # Ensure it's at least 1
            }
            
            # Add optional parameters if provided
            if country:
                params["country"] = country
            if category:
                params["category"] = category
            if query:
                params["q"] = query
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                raise APIError(f"News API returned status code {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Format response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "top_headlines",
                "is_cached": False,
                "parameters": {
                    "country": country,
                    "category": category,
                    "query": query,
                    "page": page,
                    "page_size": page_size,
                },
                "data": {
                    "total_results": data.get("totalResults", 0),
                    "articles": data.get("articles", []),
                }
            }
            
            # Add location context if available
            if self.context_manager:
                location = self.context_manager.get_current_location()
                if location:
                    result["location"] = {
                        "name": location.get("name"),
                        "country": location.get("address", {}).get("country"),
                        "country_code": location.get("address", {}).get("country_code"),
                    }
            
            # Cache the result for later
            self.cache.set(cache_key, result)
            
            return result
            
        except (requests.RequestException, ValueError, KeyError) as e:
            # Try to return cached data as fallback if available
            if self.config.get("use_fallback", True):
                # Check all caches for any news for this country/category
                fallback_data = self._get_fallback_news(country, category)
                if fallback_data:
                    fallback_data["timestamp"] = response_time
                    fallback_data["is_cached"] = True
                    fallback_data["fallback"] = True
                    fallback_data["error"] = str(e)
                    return fallback_data
            
            # No fallback available, raise the original error
            if isinstance(e, requests.RequestException):
                raise NetworkError(f"Failed to connect to news API: {str(e)}")
            raise APIError(f"Error processing news API response: {str(e)}")
    
    def _get_fallback_news(self, country: Optional[str], category: Optional[str]) -> Optional[Dict[str, Any]]:
        """Find any cached news that matches the country/category.
        
        Used for fallback when API request fails.
        
        Args:
            country: Country code or None.
            category: Category or None.
            
        Returns:
            Cached news data or None if not found.
        """
        # This is a simple implementation that only looks for exact matches in cache
        # A more advanced implementation could search for partial matches
        cache_key_parts = ["headlines"]
        if country:
            cache_key_parts.append(f"country:{country}")
        if category:
            cache_key_parts.append(f"category:{category}")
        
        # Try with specific country/category first
        specific_key = "_".join(cache_key_parts)
        specific_key += "_page:1_pageSize:10"  # Try the most common page size
        cached_data = self.cache.get(specific_key)
        if cached_data:
            return cached_data
        
        # If not found, try with just the country
        if country and category:
            country_key = f"headlines_country:{country}_page:1_pageSize:10"
            cached_data = self.cache.get(country_key)
            if cached_data:
                return cached_data
        
        # Last resort: try to find any matching headline cache
        # This would require scanning all cache entries, which is not efficient
        # For now, we'll return None
        return None
    
    @cached(ttl=3600)  # Cache for 1 hour
    def search_news(self, query: str, from_date: Optional[str] = None, to_date: Optional[str] = None,
                   language: Optional[str] = None, sort_by: str = "publishedAt",
                   page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Search for news articles.
        
        Args:
            query: Keywords or phrases to search for.
            from_date: Start date for articles in ISO format (e.g., "2023-01-01").
            to_date: End date for articles in ISO format.
            language: Language code (e.g., "en", "es", "fr").
            sort_by: Sort order ("relevancy", "popularity", "publishedAt").
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with news search results.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        
        # Get language from country if not provided
        if language is None and self.context_manager:
            country = self._get_current_country()
            # Map common country codes to language codes
            country_to_language = {
                "us": "en", "gb": "en", "au": "en", 
                "ca": "en", "fr": "fr", "de": "de", 
                "it": "it", "es": "es", "jp": "ja", 
                "kr": "ko", "cn": "zh", "ru": "ru"
            }
            language = country_to_language.get(country, "en")
        
        # Handle dates - if not provided, use sensible defaults
        if not from_date:
            # Default to a week ago if not provided
            from_date = (datetime.datetime.now(datetime.timezone.utc) - 
                      datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        if not to_date:
            # Default to today if not provided
            to_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        try:
            api_key = self._get_api_key()
            api_url = self.config.get("news_search_api_url", "https://newsapi.org/v2/everything")
            
            params = {
                "apiKey": api_key,
                "q": query,
                "from": from_date,
                "to": to_date,
                "pageSize": min(100, max(1, page_size)),
                "page": max(1, page),
            }
            
            # Add optional parameters
            if language:
                params["language"] = language
            
            if sort_by in ["relevancy", "popularity", "publishedAt"]:
                params["sortBy"] = sort_by
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                raise APIError(f"News search API returned status code {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Format response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "news_search",
                "is_cached": False,
                "parameters": {
                    "query": query,
                    "from_date": from_date,
                    "to_date": to_date,
                    "language": language,
                    "sort_by": sort_by,
                    "page": page,
                    "page_size": page_size,
                },
                "data": {
                    "total_results": data.get("totalResults", 0),
                    "articles": data.get("articles", []),
                }
            }
            
            # Add location context if available
            if self.context_manager:
                location = self.context_manager.get_current_location()
                if location:
                    result["location"] = {
                        "name": location.get("name"),
                        "country": location.get("address", {}).get("country"),
                        "country_code": location.get("address", {}).get("country_code"),
                    }
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to news search API: {str(e)}")
    
    def get_country_news(self, country: Optional[str] = None, category: Optional[str] = None,
                        page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Get news specific to a country.
        
        This is a convenience method that calls get_top_headlines with country.
        If country is not specified, uses the current country from location context.
        
        Args:
            country: Country code (ISO alpha-2) for country-specific news.
            category: Category of news (e.g., business, technology, sports).
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with country-specific news.
            
        Raises:
            NetworkError: If API request fails and no fallback is available.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        # Get country from context if not provided
        if country is None:
            country = self._get_current_country()
            
            # If still None, raise an error
            if country is None:
                raise ValueError("No country specified and no current location available")
        
        # Call get_top_headlines with the country parameter
        result = self.get_top_headlines(
            country=country,
            category=category,
            page_size=page_size,
            page=page
        )
        
        # Update the type to be more specific
        result["type"] = "country_news"
        
        return result
    
    def get_world_news(self, category: Optional[str] = None, 
                      page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Get global/world news.
        
        This method aggregates news from multiple sources or uses a global news endpoint.
        
        Args:
            category: Category of news (e.g., business, technology, sports).
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with world news.
            
        Raises:
            NetworkError: If API request fails and no fallback is available.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        response_time = self._get_current_date()
        
        # For world news, we'll use the search endpoint with broader parameters
        try:
            # First try with top sources for international news
            sources = "bbc-news,cnn,the-wall-street-journal,the-washington-post,reuters,associated-press"
            
            api_key = self._get_api_key()
            api_url = self.config.get("news_api_url", "https://newsapi.org/v2/top-headlines")
            
            params = {
                "apiKey": api_key,
                "sources": sources,
                "pageSize": min(100, max(1, page_size)),
                "page": max(1, page),
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                raise APIError(f"World news API returned status code {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Format response
            result = {
                "timestamp": response_time,
                "request_time": response_time,
                "type": "world_news",
                "is_cached": False,
                "parameters": {
                    "category": category,
                    "page": page,
                    "page_size": page_size,
                },
                "data": {
                    "total_results": data.get("totalResults", 0),
                    "articles": data.get("articles", []),
                }
            }
            
            # Add location context if available
            if self.context_manager:
                location = self.context_manager.get_current_location()
                if location:
                    result["location"] = {
                        "name": location.get("name"),
                        "country": location.get("address", {}).get("country"),
                        "country_code": location.get("address", {}).get("country_code"),
                    }
            
            # If we don't have enough results, try to supplement with general search
            if len(result["data"]["articles"]) < page_size:
                # Add a search for major world news terms
                world_terms = "global,international,world"
                if category:
                    world_terms += f",{category}"
                
                try:
                    additional_results = self.search_news(
                        query=world_terms,
                        page_size=page_size - len(result["data"]["articles"]),
                        page=1
                    )
                    
                    # Merge the results
                    if additional_results and "data" in additional_results:
                        result["data"]["articles"].extend(additional_results["data"]["articles"])
                        result["data"]["total_results"] += additional_results["data"]["total_results"]
                except Exception:
                    # Ignore errors from the supplementary search
                    pass
            
            return result
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to connect to world news API: {str(e)}")
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from a text.
        
        This can be used to find related news for a given text.
        
        Args:
            text: The text to extract keywords from.
            max_keywords: Maximum number of keywords to return.
            
        Returns:
            List of keywords extracted from the text.
        """
        # Simple keyword extraction based on word frequency
        # In a real implementation, you would use a more sophisticated approach
        # like TF-IDF or a keyword extraction API
        
        # Remove punctuation and convert to lowercase
        text = text.lower()
        for char in ".,;:!?'\"-()[]{}":
            text = text.replace(char, " ")
        
        # Split into words
        words = text.split()
        
        # Count word frequency
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Remove common stop words
        stop_words = {
            "the", "and", "a", "to", "of", "in", "is", "it", "that", "for",
            "with", "as", "was", "on", "are", "by", "this", "be", "from", "an",
            "but", "not", "or", "have", "had", "has", "what", "all", "were",
            "when", "there", "can", "been", "one", "would", "will", "more",
            "also", "who", "which", "their", "they", "about"
        }
        for word in stop_words:
            if word in word_counts:
                del word_counts[word]
        
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return the top keywords
        return [word for word, count in sorted_words[:max_keywords]]
    
    def find_related_news(self, text: str, 
                         max_keywords: int = 5, 
                         page_size: int = 10, 
                         page: int = 1) -> Dict[str, Any]:
        """Find news related to a given text.
        
        Extracts keywords from the text and searches for news containing those keywords.
        
        Args:
            text: The text to find related news for.
            max_keywords: Maximum number of keywords to extract.
            page_size: Number of results to return per page.
            page: Page number for results pagination.
            
        Returns:
            Dictionary with related news.
            
        Raises:
            NetworkError: If API request fails.
            APIError: If API returns an error.
            MissingAPIKeyError: If API key is not found.
        """
        # Extract keywords from the text
        keywords = self.extract_keywords(text, max_keywords)
        
        # If no keywords could be extracted, raise an error
        if not keywords:
            raise ValueError("No keywords could be extracted from the text")
        
        # Build a query from the keywords
        query = " OR ".join(keywords)
        
        # Search for news with the query
        result = self.search_news(
            query=query,
            page_size=page_size,
            page=page
        )
        
        # Update the type and add the keywords
        result["type"] = "related_news"
        result["keywords"] = keywords
        
        return result