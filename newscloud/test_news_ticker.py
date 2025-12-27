"""
Expanded unit tests for News Ticker.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import sys
import warnings
from datetime import datetime, timedelta
import pygame

# Suppress urllib3 NotOpenSSLWarning
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*OpenSSL.*")

# Mock pygame before importing anything that uses it if needed,
# though here we are importing from news_ticker which initializes it.
from news_ticker import NewsFetcher, get_api_key, Headline


class TestNewsTicker(unittest.TestCase):
    """
    Test cases for NewsFetcher, Headline, and utility functions.
    """

    def setUp(self):
        self.api_key = "test_key"
        self.fetcher = NewsFetcher(self.api_key)
        if os.path.exists("headlines_cached.json"):
            os.remove("headlines_cached.json")
        # Ensure icons dir doesn't interfere
        if not os.path.exists("icons"):
            os.makedirs("icons")

    def tearDown(self):
        if os.path.exists("headlines_cached.json"):
            os.remove("headlines_cached.json")

    # --- NewsFetcher Tests ---

    @patch("requests.get")
    def test_fetch_headlines_no_cache(self, mock_get):
        """Test fetching headlines when no cache exists."""
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
    def test_fetch_headlines_api_error(self, mock_get):
        """Test NewsFetcher handles API errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        with self.assertRaises(Exception):
            self.fetcher.fetch_headlines(cache=False)

    @patch("pygame.image.load")
    @patch("os.path.exists")
    def test_get_favicon_cache_hit(self, mock_exists, mock_load):
        """Test get_favicon returns cached image if available."""
        mock_exists.return_value = True
        mock_load.return_value = MagicMock(spec=pygame.Surface)

        result = self.fetcher.get_favicon("https://example.com/item")
        self.assertIsNotNone(result)
        mock_load.assert_called_once()

    @patch("requests.get")
    @patch("pygame.image.load")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_favicon_fetch_success(
        self, mock_file, mock_exists, mock_load, mock_get
    ):
        """Test get_favicon fetches and caches a new icon."""
        mock_exists.return_value = False
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"fake_image_data"
        mock_get.return_value = mock_resp
        mock_load.return_value = MagicMock(spec=pygame.Surface)

        result = self.fetcher.get_favicon("https://newsite.com")
        self.assertIsNotNone(result)
        mock_get.assert_called_once()
        mock_file.assert_called()

    # --- get_api_key Tests ---

    def test_get_api_key_cmd(self):
        """Test retrieving API key from command line argument."""
        key = get_api_key("cmd_key")
        self.assertEqual(key, "cmd_key")

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="file_key")
    def test_get_api_key_file(self, mock_file, mock_exists):
        """Test retrieving API key from file."""
        mock_exists.return_value = True
        key = get_api_key()
        self.assertEqual(key, "file_key")
        mock_file.assert_called_with("newsapikey.txt", "r")

    @patch("os.path.exists")
    def test_get_api_key_none(self, mock_exists):
        """Test returning None if no key found."""
        mock_exists.return_value = False
        key = get_api_key()
        self.assertIsNone(key)

    # --- Headline Tests ---

    @patch("pygame.font.SysFont")
    def test_headline_age_calc(self, mock_font):
        """Test human readable age calculation."""
        # Setup mock font
        mock_font_obj = MagicMock()
        mock_surf = MagicMock(spec=pygame.Surface)
        mock_surf.get_width.return_value = 100
        mock_surf.get_height.return_value = 20
        mock_font_obj.render.return_value = mock_surf
        
        now = datetime.now().astimezone()

        # Case 1: Minutes ago
        five_m_ago = (now - timedelta(minutes=5)).isoformat()
        h1 = Headline({"publishedAt": five_m_ago}, mock_font_obj, mock_font_obj, 0, 0)
        self.assertEqual(h1.age_str, "5m ago")

        # Case 2: Hours ago
        two_h_ago = (now - timedelta(hours=2)).isoformat()
        h2 = Headline({"publishedAt": two_h_ago}, mock_font_obj, mock_font_obj, 0, 0)
        self.assertEqual(h2.age_str, "2h ago")

        # Case 3: Days ago
        three_d_ago = (now - timedelta(days=3)).isoformat()
        h3 = Headline({"publishedAt": three_d_ago}, mock_font_obj, mock_font_obj, 0, 0)
        self.assertEqual(h3.age_str, "3d ago")

        # Case 4: Malformed date
        h4 = Headline({"publishedAt": "invalid-date"}, mock_font_obj, mock_font_obj, 0, 0)
        self.assertEqual(h4.age_str, "Recently")


if __name__ == "__main__":
    # Initialize pygame for font tests
    pygame.init()
    unittest.main()
