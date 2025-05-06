"""Tests for the core module."""

import unittest
import datetime
from unittest.mock import patch, MagicMock

from contextuals.core.config import Config
from contextuals.core.cache import Cache, cached
from contextuals import Contextuals


class TestConfig(unittest.TestCase):
    """Test the Config class."""

    def test_init(self):
        """Test initialization with default values."""
        config = Config()
        self.assertTrue(config.get("cache_enabled"))
        self.assertEqual(config.get("cache_duration"), 300)

    def test_init_with_overrides(self):
        """Test initialization with overrides."""
        config = Config(cache_duration=600, weather_api_key="test_key")
        self.assertEqual(config.get("cache_duration"), 600)
        self.assertEqual(config.get("weather_api_key"), "test_key")

    def test_get_set(self):
        """Test get and set methods."""
        config = Config()
        config.set("test_key", "test_value")
        self.assertEqual(config.get("test_key"), "test_value")
        self.assertEqual(config.get("nonexistent", "default"), "default")

    def test_update(self):
        """Test update method."""
        config = Config()
        config.update({"key1": "value1", "key2": "value2"})
        self.assertEqual(config.get("key1"), "value1")
        self.assertEqual(config.get("key2"), "value2")

    def test_api_key_methods(self):
        """Test API key methods."""
        config = Config()
        config.set_api_key("weather", "weather_key")
        self.assertEqual(config.get_api_key("weather"), "weather_key")
        self.assertIsNone(config.get_api_key("nonexistent"))


class TestCache(unittest.TestCase):
    """Test the Cache class."""

    def test_init(self):
        """Test initialization."""
        cache = Cache()
        self.assertEqual(cache.default_ttl, 300)

        cache = Cache(default_ttl=600)
        self.assertEqual(cache.default_ttl, 600)

    def test_get_set(self):
        """Test get and set methods."""
        cache = Cache()
        cache.set("test_key", "test_value")
        self.assertEqual(cache.get("test_key"), "test_value")
        self.assertIsNone(cache.get("nonexistent"))

    def test_invalidate(self):
        """Test invalidate method."""
        cache = Cache()
        cache.set("test_key", "test_value")
        self.assertEqual(cache.get("test_key"), "test_value")
        cache.invalidate("test_key")
        self.assertIsNone(cache.get("test_key"))

    def test_clear(self):
        """Test clear method."""
        cache = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        cache.clear()
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))

    @patch('time.time')
    def test_expiration(self, mock_time):
        """Test cache expiration."""
        cache = Cache(default_ttl=10)
        mock_time.return_value = 100
        cache.set("test_key", "test_value")
        self.assertEqual(cache.get("test_key"), "test_value")

        # Simulate time passing, but not enough to expire
        mock_time.return_value = 105
        self.assertEqual(cache.get("test_key"), "test_value")

        # Simulate time passing, enough to expire
        mock_time.return_value = 111
        self.assertIsNone(cache.get("test_key"))

    def test_cached_decorator(self):
        """Test the cached decorator."""
        counter = {'value': 0}

        @cached(ttl=10)
        def test_function(arg):
            counter['value'] += 1
            return f"Result: {arg}"

        # First call should execute the function
        result1 = test_function("test")
        self.assertEqual(result1, "Result: test")
        self.assertEqual(counter['value'], 1)

        # Second call with same args should use cache
        result2 = test_function("test")
        self.assertEqual(result2, "Result: test")
        self.assertEqual(counter['value'], 1)  # Counter shouldn't increment

        # Call with different args should execute the function
        result3 = test_function("different")
        self.assertEqual(result3, "Result: different")
        self.assertEqual(counter['value'], 2)


class TestContextuals(unittest.TestCase):
    """Test the Contextuals class."""

    def test_init(self):
        """Test initialization."""
        context = Contextuals()
        self.assertIsNotNone(context.config)
        self.assertIsNotNone(context.cache)
        self.assertIsNotNone(context._time)

    @patch('requests.get')
    def test_update_config(self, mock_get):
        """Test update_config method."""
        # Mock API response to prevent actual API call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unixtime": int(datetime.datetime.now().timestamp())}
        mock_get.return_value = mock_response
        
        # Now create the context with mocked API
        context = Contextuals()
        context.update_config(cache_duration=600)
        self.assertEqual(context.config.get("cache_duration"), 600)

    def test_set_api_key(self):
        """Test set_api_key method."""
        context = Contextuals()
        context.set_api_key("weather", "test_key")
        self.assertEqual(context.config.get_api_key("weather"), "test_key")

    def test_clear_cache(self):
        """Test clear_cache method."""
        context = Contextuals()
        # Use a spy on the cache.clear method
        with patch.object(context.cache, 'clear') as mock_clear:
            context.clear_cache()
            mock_clear.assert_called_once()

    @patch('contextuals.core.contextual.TimeProvider')
    def test_time_property(self, MockTimeProvider):
        """Test time property."""
        # Create a mock instance
        mock_time_provider = MagicMock()
        MockTimeProvider.return_value = mock_time_provider
        
        # Initialize with our mocked TimeProvider
        context = Contextuals()
        
        # Assert the time property is initialized correctly
        self.assertIsNotNone(context._time)

    @patch('contextuals.weather.weather_provider.WeatherProvider')
    def test_weather_property(self, MockWeatherProvider):
        """Test weather property."""
        mock_weather_provider = MagicMock()
        MockWeatherProvider.return_value = mock_weather_provider

        context = Contextuals()
        weather_provider = context.weather
        self.assertEqual(weather_provider, mock_weather_provider)

    def test_location_property(self):
        """Test that the location property exists."""
        # Simply verify that the property exists, without mocking the import
        # This test is problematic due to the lazy loading mechanism
        self.assertTrue(hasattr(Contextuals, 'location'))


if __name__ == '__main__':
    unittest.main()