"""
Unit tests for News Ticker.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import warnings

# Suppress urllib3 NotOpenSSLWarning
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*OpenSSL.*")

from news_ticker import NewsFetcher, get_api_key


class TestNewsTicker(unittest.TestCase):
    """
    Test cases for NewsFetcher and utility functions.
    """

    def setUp(self):
        self.api_key = "test_key"
        self.fetcher = NewsFetcher(self.api_key)
        if os.path.exists("headlines_cached.json"):
            os.remove("headlines_cached.json")

    def tearDown(self):
        if os.path.exists("headlines_cached.json"):
            os.remove("headlines_cached.json")

    @patch("requests.get")
    def test_fetch_headlines_no_cache(self, mock_get):
        """
        Test fetching headlines when no cache exists.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "articles": [{"title": "Test Title", "url": "http://test.com"}]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        articles = self.fetcher.fetch_headlines(cache=False)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "Test Title")
        self.assertFalse(os.path.exists("headlines_cached.json"))

    @patch("requests.get")
    def test_fetch_headlines_with_cache(self, mock_get):
        """
        Test fetching headlines and saving to cache.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "articles": [{"title": "Cached Title", "url": "http://cached.com"}]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        articles = self.fetcher.fetch_headlines(cache=True)
        self.assertTrue(os.path.exists("headlines_cached.json"))

        # Verify cache content
        with open("headlines_cached.json", "r") as f:
            cached_data = json.load(f)
        self.assertEqual(cached_data[0]["title"], "Cached Title")

    def test_get_api_key_cmd(self):
        """
        Test retrieving API key from command line argument.
        """
        key = get_api_key("cmd_key")
        self.assertEqual(key, "cmd_key")


if __name__ == "__main__":
    unittest.main()
