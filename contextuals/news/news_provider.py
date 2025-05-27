"""RSS-based news provider for Contextuals."""

import datetime
import json
import re
import warnings
import xml.sax
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse, urljoin
import requests
import feedparser

from contextuals.core.cache import Cache, cached
from contextuals.core.config import Config
from contextuals.core.exceptions import APIError, NetworkError, MissingAPIKeyError


class NewsProvider:
    """Provides news-related contextual information using RSS feeds.
    
    Features:
    - Retrieves news from reputable RSS sources (BBC, Reuters, Google News, etc.)
    - No API keys required - completely free
    - Filters news by country, category, or topic
    - Caches results to minimize network calls
    - Provides fallback data when offline
    - Returns structured JSON responses with timestamps
    - Uses location awareness for country-specific news
    - Maintains backward compatibility with NewsAPI format
    """
    
    # RSS Feed Sources - organized by type and country
    RSS_SOURCES = {
        "world": {
            "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "reuters": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
            "google": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "ap": "https://rsshub.app/ap/topics/apf-topnews",
            "hackernews": "https://hnrss.org/frontpage"
        },
        "country": {
            "us": {
                "general": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
                "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
                "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y0RRU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
                "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdRU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en",
                "health": "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en"
            },
            "gb": {
                "general": "https://feeds.bbci.co.uk/news/rss.xml",
                "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
                "technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
                "sports": "https://feeds.bbci.co.uk/sport/rss.xml",
                "health": "https://feeds.bbci.co.uk/news/health/rss.xml"
            },
            "fr": {
                "general": "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr",
                "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0FtWnlHZ0pHVWlnQVAB?hl=fr&gl=FR&ceid=FR:fr",
                "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y0RRU0FtWnlHZ0pHVWlnQVAB?hl=fr&gl=FR&ceid=FR:fr",
                "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdRU0FtWnlHZ0pHVWlnQVAB?hl=fr&gl=FR&ceid=FR:fr"
            },
            "de": {
                "general": "https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de",
                "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0FtUmxHZ0pFUlNnQVAB?hl=de&gl=DE&ceid=DE:de",
                "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y0RRU0FtUmxHZ0pFUlNnQVAB?hl=de&gl=DE&ceid=DE:de",
                "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdRU0FtUmxHZ0pFUlNnQVAB?hl=de&gl=DE&ceid=DE:de"
            },
            "ca": {
                "general": "https://news.google.com/rss?hl=en-CA&gl=CA&ceid=CA:en",
                "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0FtVnVHZ0pEUVNnQVAB?hl=en-CA&gl=CA&ceid=CA:en",
                "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y0RRU0FtVnVHZ0pEUVNnQVAB?hl=en-CA&gl=CA&ceid=CA:en",
                "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdRU0FtVnVHZ0pEUVNnQVAB?hl=en-CA&gl=CA&ceid=CA:en"
            },
            "au": {
                "general": "https://news.google.com/rss?hl=en-AU&gl=AU&ceid=AU:en",
                "business": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZ4ZERBU0FtVnVHZ0pCVlNnQVAB?hl=en-AU&gl=AU&ceid=AU:en",
                "technology": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y0RRU0FtVnVHZ0pCVlNnQVAB?hl=en-AU&gl=AU&ceid=AU:en",
                "sports": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdRU0FtVnVHZ0pCVlNnQVAB?hl=en-AU&gl=AU&ceid=AU:en"
            }
        }
    }
    
    def __init__(self, config: Config, cache: Cache, context_manager=None):
        """Initialize the RSS-based news provider.
        
        Args:
            config: Configuration instance.
            cache: Cache instance.
            context_manager: Optional context manager instance.
        """
        self.config = config
        self.cache = cache
        self.context_manager = context_manager
        
        # Issue deprecation warning for NewsAPI
        if config.get_api_key("news"):
            warnings.warn(
                "NewsAPI is deprecated in favor of RSS feeds. "
                "RSS feeds are free, require no API key, and have no rate limits. "
                "The CONTEXTUALS_NEWS_API_KEY environment variable is no longer needed.",
                DeprecationWarning,
                stacklevel=2
            )
    
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
    
    def _parse_rss_feed(self, url: str, max_articles: int = 10) -> List[Dict[str, Any]]:
        """Parse an RSS feed and extract articles.
        
        Args:
            url: RSS feed URL
            max_articles: Maximum number of articles to return
            
        Returns:
            List of article dictionaries with NewsAPI-compatible format
        """
        try:
            # Parse the RSS feed
            feed = feedparser.parse(url)
            
            if feed.bozo and feed.bozo_exception:
                # Feed has parsing errors, but might still be usable
                # Only warn for critical errors, not common XML formatting issues
                if not isinstance(feed.bozo_exception, (xml.sax.SAXParseException, UnicodeDecodeError)):
                    warnings.warn(f"RSS feed parsing warning for {url}: {feed.bozo_exception}")
            
            articles = []
            
            for entry in feed.entries[:max_articles]:
                # Extract article data in NewsAPI-compatible format
                article = {
                    "title": entry.get("title", "").strip(),
                    "description": self._extract_description(entry),
                    "url": entry.get("link", ""),
                    "urlToImage": self._extract_image(entry),
                    "publishedAt": self._parse_date(entry),
                    "source": {
                        "id": self._extract_source_id(url),
                        "name": feed.feed.get("title", self._extract_source_name(url))
                    },
                    "author": entry.get("author", ""),
                    "content": self._extract_content(entry)
                }
                
                # Only add articles with valid title and URL
                if article["title"] and article["url"]:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            warnings.warn(f"Failed to parse RSS feed {url}: {str(e)}")
            return []
    
    def _extract_description(self, entry) -> str:
        """Extract description from RSS entry."""
        # Try different fields for description
        description = (
            entry.get("summary", "") or 
            entry.get("description", "") or 
            entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
        )
        
        # Clean HTML tags if present
        if description:
            description = re.sub(r'<[^>]+>', '', description).strip()
            # Limit description length
            if len(description) > 300:
                description = description[:297] + "..."
        
        return description
    
    def _extract_image(self, entry) -> Optional[str]:
        """Extract image URL from RSS entry."""
        # Try different fields for images
        image_url = None
        
        # Check media content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    image_url = media.get('url')
                    break
        
        # Check enclosures
        if not image_url and hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href')
                    break
        
        # Check media thumbnail
        if not image_url and hasattr(entry, 'media_thumbnail'):
            if entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get('url')
        
        # Extract from content/summary (basic regex)
        if not image_url:
            content = entry.get("summary", "") + entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            if img_match:
                image_url = img_match.group(1)
        
        return image_url
    
    def _parse_date(self, entry) -> str:
        """Parse and format publication date."""
        # Try different date fields
        date_str = entry.get("published", "") or entry.get("updated", "")
        
        if date_str:
            try:
                # feedparser usually provides parsed time
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    dt = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
                    return dt.isoformat()
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    dt = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
                    return dt.isoformat()
            except (ValueError, TypeError):
                pass
        
        # Fallback to current time
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    def _extract_source_id(self, url: str) -> str:
        """Extract source identifier from URL."""
        domain = urlparse(url).netloc.lower()
        
        # Map common domains to source IDs
        source_map = {
            "feeds.bbci.co.uk": "bbc-news",
            "news.google.com": "google-news",
            "reutersagency.com": "reuters",
            "rsshub.app": "associated-press",
            "hnrss.org": "hacker-news"
        }
        
        return source_map.get(domain, domain.replace("www.", "").replace(".", "-"))
    
    def _extract_source_name(self, url: str) -> str:
        """Extract source name from URL."""
        domain = urlparse(url).netloc.lower()
        
        # Map common domains to readable names
        name_map = {
            "feeds.bbci.co.uk": "BBC News",
            "news.google.com": "Google News",
            "reutersagency.com": "Reuters",
            "rsshub.app": "Associated Press",
            "hnrss.org": "Hacker News"
        }
        
        return name_map.get(domain, domain.replace("www.", "").title())
    
    def _extract_content(self, entry) -> str:
        """Extract content snippet from RSS entry."""
        content = ""
        
        if entry.get("content"):
            content = entry.content[0].get("value", "")
        elif entry.get("summary"):
            content = entry.summary
        
        # Clean HTML and limit length
        if content:
            content = re.sub(r'<[^>]+>', '', content).strip()
            if len(content) > 500:
                content = content[:497] + "..."
        
        return content
    
    def _get_rss_urls_for_country(self, country: str, category: Optional[str] = None) -> List[str]:
        """Get RSS URLs for a specific country and category.
        
        Args:
            country: Country code (ISO alpha-2)
            category: News category (optional)
            
        Returns:
            List of RSS URLs
        """
        urls = []
        country = country.lower()
        
        # Get country-specific feeds
        if country in self.RSS_SOURCES["country"]:
            country_feeds = self.RSS_SOURCES["country"][country]
            
            if category and category in country_feeds:
                urls.append(country_feeds[category])
            elif "general" in country_feeds:
                urls.append(country_feeds["general"])
        
        # Fallback to world feeds if no country-specific feeds
        if not urls:
            if country == "us":
                urls.append(self.RSS_SOURCES["world"]["google"])
            else:
                urls.extend([
                    self.RSS_SOURCES["world"]["bbc"],
                    self.RSS_SOURCES["world"]["reuters"]
                ])
        
        return urls
    
    def _get_world_rss_urls(self, category: Optional[str] = None) -> List[str]:
        """Get RSS URLs for world news.
        
        Args:
            category: News category (optional)
            
        Returns:
            List of RSS URLs
        """
        # Use reputable international sources
        urls = [
            self.RSS_SOURCES["world"]["bbc"],
            self.RSS_SOURCES["world"]["reuters"],
            self.RSS_SOURCES["world"]["ap"]
        ]
        
        # Add tech-specific source for technology category
        if category == "technology":
            urls.append(self.RSS_SOURCES["world"]["hackernews"])
        
        return urls
    
    @cached(ttl=1800)  # Cache for 30 minutes
    def get_top_headlines(self, country: Optional[str] = None, category: Optional[str] = None, 
                         query: Optional[str] = None, page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Get top news headlines using RSS feeds.
        
        If country is not specified, uses the current country from location context.
        
        Args:
            country: Country code (ISO alpha-2) for country-specific news.
            category: Category of news (e.g., business, technology, sports).
            query: Keywords or phrases to search for (basic filtering).
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with news headline information in NewsAPI-compatible format.
            
        Raises:
            NetworkError: If RSS feeds fail and no fallback is available.
        """
        response_time = self._get_current_date()
        
        # Get country from context if not provided
        if country is None:
            country = self._get_current_country()
        
        # Ensure country code is lowercase
        if country:
            country = country.lower()
        
        # Create cache key based on parameters
        cache_key_parts = ["rss_headlines"]
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
        
        # Get RSS URLs for the request
        if country:
            rss_urls = self._get_rss_urls_for_country(country, category)
        else:
            rss_urls = self._get_world_rss_urls(category)
        
        # Fetch articles from RSS feeds
        all_articles = []
        
        for url in rss_urls:
            try:
                articles = self._parse_rss_feed(url, max_articles=page_size)
                all_articles.extend(articles)
            except Exception as e:
                warnings.warn(f"Failed to fetch from RSS feed {url}: {str(e)}")
                continue
        
        # Filter by query if provided
        if query and all_articles:
            query_lower = query.lower()
            filtered_articles = []
            for article in all_articles:
                if (query_lower in article.get("title", "").lower() or 
                    query_lower in article.get("description", "").lower()):
                    filtered_articles.append(article)
            all_articles = filtered_articles
        
        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_articles = all_articles[start_idx:end_idx]
        
        # Format response in NewsAPI-compatible format
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
                "status": "ok",
                "totalResults": len(all_articles),
                "articles": paginated_articles,
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
    
    def _get_fallback_news(self, country: Optional[str], category: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get fallback news data from cache.
        
        Args:
            country: Country code for fallback search.
            category: Category for fallback search.
            
        Returns:
            Cached news data if available, None otherwise.
        """
        # Try to find any cached news for this country/category combination
        cache_patterns = [
            f"rss_headlines_country:{country}_category:{category}",
            f"rss_headlines_country:{country}",
            f"rss_headlines_category:{category}",
            "rss_headlines"
        ]
        
        for pattern in cache_patterns:
            # Look for any cache key that matches the pattern
            for key in self.cache._cache.keys():
                if pattern in key:
                    cached_data = self.cache.get(key)
                    if cached_data:
                        return cached_data
        
        return None
    
    @cached(ttl=3600)  # Cache for 1 hour
    def search_news(self, query: str, from_date: Optional[str] = None, to_date: Optional[str] = None,
                   language: Optional[str] = None, sort_by: str = "publishedAt",
                   page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Search for news articles using RSS feeds.
        
        Note: RSS feeds have limited search capabilities compared to NewsAPI.
        This method fetches recent articles and filters them locally.
        
        Args:
            query: Keywords or phrases to search for.
            from_date: Start date for search (limited support in RSS).
            to_date: End date for search (limited support in RSS).
            language: Language for search (limited support in RSS).
            sort_by: Sort order (publishedAt, relevancy, popularity).
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with search results in NewsAPI-compatible format.
            
        Raises:
            NetworkError: If RSS feeds fail and no fallback is available.
        """
        response_time = self._get_current_date()
        
        # Create cache key
        cache_key = f"rss_search_q:{query}_page:{page}_pageSize:{page_size}"
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            result = cached_data.copy()
            result["timestamp"] = response_time
            result["is_cached"] = True
            return result
        
        # Get articles from multiple RSS sources
        all_articles = []
        
        # Use world news sources for search
        rss_urls = self._get_world_rss_urls()
        
        # Add Google News search URL if possible
        google_search_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        rss_urls.insert(0, google_search_url)
        
        for url in rss_urls:
            try:
                articles = self._parse_rss_feed(url, max_articles=20)  # Get more for filtering
                all_articles.extend(articles)
            except Exception as e:
                warnings.warn(f"Failed to fetch from RSS feed {url}: {str(e)}")
                continue
        
        # Filter articles by query
        query_lower = query.lower()
        filtered_articles = []
        
        for article in all_articles:
            relevance_score = 0
            title = article.get("title", "").lower()
            description = article.get("description", "").lower()
            content = article.get("content", "").lower()
            
            # Calculate relevance score
            if query_lower in title:
                relevance_score += 3
            if query_lower in description:
                relevance_score += 2
            if query_lower in content:
                relevance_score += 1
            
            # Check for individual query terms
            query_terms = query_lower.split()
            for term in query_terms:
                if term in title:
                    relevance_score += 1
                if term in description:
                    relevance_score += 0.5
            
            if relevance_score > 0:
                article["_relevance_score"] = relevance_score
                filtered_articles.append(article)
        
        # Sort by relevance or date
        if sort_by == "relevancy":
            filtered_articles.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
        else:  # publishedAt
            filtered_articles.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        
        # Remove relevance score from final results
        for article in filtered_articles:
            article.pop("_relevance_score", None)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_articles = filtered_articles[start_idx:end_idx]
        
        # Format response
        result = {
            "timestamp": response_time,
            "request_time": response_time,
            "type": "search_results",
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
                "status": "ok",
                "totalResults": len(filtered_articles),
                "articles": paginated_articles,
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
        
        # Cache the result
        self.cache.set(cache_key, result)
        
        return result
    
    def get_country_news(self, country: Optional[str] = None, category: Optional[str] = None,
                        page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """Get news specific to a country using RSS feeds.
        
        This is a convenience method that calls get_top_headlines with country.
        If country is not specified, uses the current country from location context.
        
        Args:
            country: Country code (ISO alpha-2) for country-specific news.
            category: Category of news (e.g., business, technology, sports).
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with country-specific news in NewsAPI-compatible format.
            
        Raises:
            NetworkError: If RSS feeds fail and no fallback is available.
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
        """Get global/world news using RSS feeds.
        
        This method aggregates news from multiple reputable international RSS sources.
        
        Args:
            category: Category of news (e.g., business, technology, sports).
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with world news in NewsAPI-compatible format.
            
        Raises:
            NetworkError: If RSS feeds fail and no fallback is available.
        """
        response_time = self._get_current_date()
        
        # Create cache key
        cache_key_parts = ["rss_world_news"]
        if category:
            cache_key_parts.append(f"category:{category}")
        cache_key_parts.append(f"page:{page}")
        cache_key_parts.append(f"pageSize:{page_size}")
        cache_key = "_".join(cache_key_parts)
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data:
            result = cached_data.copy()
            result["timestamp"] = response_time
            result["is_cached"] = True
            return result
        
        # Get world RSS URLs
        rss_urls = self._get_world_rss_urls(category)
        
        # Fetch articles from RSS feeds
        all_articles = []
        
        for url in rss_urls:
            try:
                articles = self._parse_rss_feed(url, max_articles=page_size)
                all_articles.extend(articles)
            except Exception as e:
                warnings.warn(f"Failed to fetch from RSS feed {url}: {str(e)}")
                continue
        
        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_articles = all_articles[start_idx:end_idx]
        
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
                "status": "ok",
                "totalResults": len(all_articles),
                "articles": paginated_articles,
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
        
        # Cache the result
        self.cache.set(cache_key, result)
        
        return result
    
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
        """Find news articles related to the given text using RSS feeds.
        
        This method extracts keywords from the text and searches for related news.
        
        Args:
            text: The text to find related news for.
            max_keywords: Maximum number of keywords to extract for search.
            page_size: Number of results to return per page (1-100).
            page: Page number for results pagination.
            
        Returns:
            Dictionary with related news articles in NewsAPI-compatible format.
        """
        # Extract keywords from the text
        keywords = self.extract_keywords(text, max_keywords)
        
        if not keywords:
            # Return empty result if no keywords found
            return {
                "timestamp": self._get_current_date(),
                "request_time": self._get_current_date(),
                "type": "related_news",
                "is_cached": False,
                "parameters": {
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "max_keywords": max_keywords,
                    "page": page,
                    "page_size": page_size,
                },
                "data": {
                    "status": "ok",
                    "totalResults": 0,
                    "articles": [],
                    "keywords_used": keywords
                }
            }
        
        # Search for news using the extracted keywords
        query = " ".join(keywords[:3])  # Use top 3 keywords for search
        
        result = self.search_news(
            query=query,
            page_size=page_size,
            page=page
        )
        
        # Update the type and add keywords info
        result["type"] = "related_news"
        result["parameters"]["text"] = text[:100] + "..." if len(text) > 100 else text
        result["parameters"]["max_keywords"] = max_keywords
        result["data"]["keywords_used"] = keywords
        
        return result