import os
import sys
import json
import time
import argparse
import webbrowser
import warnings
import random
from datetime import datetime
from urllib.parse import urlparse
from threading import Thread
from io import BytesIO

# Suppress urllib3 NotOpenSSLWarning which occurs on some macOS systems with older LibreSSL
# Must be done before importing requests/urllib3
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", message=".*OpenSSL.*")

import requests
import pygame

# Constants
CACHE_FILE = "headlines_cached.json"
API_KEY_FILE = "newsapikey.txt"
ICON_DIR = "icons"
UPDATE_INTERVAL = 3600  # 1 hour in seconds
BG_COLOR = (10, 10, 15)
TEXT_COLOR = (240, 240, 240)
HOVER_COLOR = (0, 191, 255)
INFO_COLOR = (180, 180, 180)
TOOLTIP_BG = (30, 31, 40, 230)
FONT_SIZE = 26
TICKER_SPEED = 2.0
FPS = 60
LANES = 5
LANE_HEIGHT = 60
SCREEN_HEIGHT = LANES * LANE_HEIGHT + 20

# License Text for MPL 2.0 (Shortened for Header)
LICENSE_HEADER = """
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


class Headline:
    """
    Represents a single news headline in the ticker.

    Attributes
    ----------
    text : str
        The headline text.
    url : str
        The URL to the full article.
    x : float
        The current horizontal position.
    y : float
        The vertical position.
    width : int
        The width of the rendered text.
    rect : pygame.Rect
        The bounding rectangle for collision detection.
    age : str
        Human readable age of the article.
    description : str
        Article description for tooltip.
    icon : pygame.Surface
        Favicon for the news source.
    """

    def __init__(self, data, font, small_font, x, y, icon_surface=None):
        """
        Initialize a Headline object.

        Parameters
        ----------
        data : dict
            Article data from API.
        font : pygame.font.Font
            Font for the headline.
        small_font : pygame.font.Font
            Font for the tooltip info.
        x : float
            Starting x position.
        y : float
            Vertical position.
        icon_surface : pygame.Surface, optional
            Pre-loaded icon.
        """
        self.text = data.get("title", "No Title")
        self.url = data.get("url", "")
        self.description = data.get("description") or "No description available."
        self.published_at = data.get("publishedAt")
        self.x = x
        self.y = y
        self.icon = icon_surface

        # Calculate age
        self.age_str = "Recently"
        if self.published_at:
            try:
                dt = datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
                diff = datetime.now().astimezone() - dt
                hours = int(diff.total_seconds() // 3600)
                if hours < 1:
                    mins = int(diff.total_seconds() // 60)
                    self.age_str = f"{mins}m ago"
                elif hours < 24:
                    self.age_str = f"{hours}h ago"
                else:
                    self.age_str = f"{hours // 24}d ago"
            except Exception:
                pass

        self.surface = font.render(self.text, True, TEXT_COLOR)
        self.hover_surface = font.render(self.text, True, HOVER_COLOR)

        # Icon offset
        self.text_offset = 32 if self.icon else 0
        self.width = self.surface.get_width() + self.text_offset
        self.height = max(self.surface.get_height(), 24)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, speed):
        """Update x position."""
        self.x -= speed
        self.rect.x = self.x

    def draw(self, screen, mouse_pos, font_small):
        """Draw headline and icon. Returns True if hovering."""
        is_hover = self.rect.collidepoint(mouse_pos)

        # Draw icon
        if self.icon:
            screen.blit(
                self.icon,
                (self.x, self.y + (self.height - self.icon.get_height()) // 2),
            )

        # Draw text
        surf = self.hover_surface if is_hover else self.surface
        screen.blit(surf, (self.x + self.text_offset, self.y))

        return is_hover

    def draw_tooltip(self, screen, mouse_pos, font_small):
        """Draw tooltip with age and description."""
        padding = 10
        max_tool_width = 400

        info_text = f"[{self.age_str}] {self.description}"

        # Word wrap for description
        words = info_text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font_small.size(test_line)[0] < max_tool_width - (padding * 2):
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        # Calculate tooltip height
        lh = font_small.get_linesize()
        tw = max_tool_width
        th = len(lines) * lh + (padding * 2)

        # Position tooltip above mouse
        tx = mouse_pos[0]
        ty = mouse_pos[1] - th - 10

        # Keep tooltip on screen
        if tx + tw > screen.get_width():
            tx = screen.get_width() - tw
        if tx < 0:
            tx = 0
        if ty < 0:
            ty = mouse_pos[1] + 20

        # Draw tooltip background (with alpha)
        s = pygame.Surface((tw, th), pygame.SRCALPHA)
        s.fill(TOOLTIP_BG)
        screen.blit(s, (tx, ty))

        # Draw lines
        for i, line in enumerate(lines):
            lsurf = font_small.render(line.strip(), True, INFO_COLOR)
            screen.blit(lsurf, (tx + padding, ty + padding + i * lh))


class NewsFetcher:
    """Handles interactions with the NewsAPI and icon fetching."""

    def __init__(self, api_key, params_override=None):
        self.api_key = api_key
        self.params = {"pageSize": 100, "apiKey": self.api_key}
        if params_override:
            self.params.update(params_override)
        if not os.path.exists(ICON_DIR):
            os.makedirs(ICON_DIR)

    def fetch_headlines(self, cache=True):
        """Fetch news from API or local json cache."""
        if cache and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        url = "https://newsapi.org/v2/top-headlines"
        response = requests.get(url, params=self.params)
        response.raise_for_status()
        articles = response.json().get("articles", [])

        if cache:
            with open(CACHE_FILE, "w") as f:
                json.dump(articles, f)
        return articles

    def get_valid_options(self):
        """Fetch valid NewsAPI params."""
        url = "https://newsapi.org/v2/top-headlines/sources"
        response = requests.get(url, params={"apiKey": self.api_key})
        response.raise_for_status()
        sources = response.json().get("sources", [])
        return {
            "countries": sorted(list({s["country"] for s in sources})),
            "categories": sorted(list({s["category"] for s in sources})),
            "sources": sorted(list({s["id"] for s in sources})),
        }

    def get_favicon(self, article_url):
        """Fetch and cache favicon for a domain."""
        domain = urlparse(article_url).netloc
        if not domain:
            return None

        safe_domain = domain.replace(".", "_")
        icon_path = os.path.join(ICON_DIR, f"{safe_domain}.png")

        if os.path.exists(icon_path):
            try:
                return pygame.image.load(icon_path)
            except Exception:
                pass

        # Try Google's favicon service
        try:
            fav_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
            resp = requests.get(fav_url, timeout=5)
            if resp.status_code == 200:
                with open(icon_path, "wb") as f:
                    f.write(resp.content)
                return pygame.image.load(BytesIO(resp.content))
        except Exception:
            pass
        return None


def get_api_key(cmd_key=None):
    if cmd_key:
        return cmd_key
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return None


class NewsTickerApp:
    """Main application manager."""

    def __init__(self, fetcher):
        pygame.init()
        self.fetcher = fetcher
        self.screen = pygame.display.set_mode((1200, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("News Ticker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Outfit", FONT_SIZE) or pygame.font.SysFont(
            "Arial", FONT_SIZE
        )
        self.small_font = pygame.font.SysFont("Outfit", 18) or pygame.font.SysFont(
            "Arial", 16
        )

        self.headlines = []
        self.lane_last_x = [0] * LANES
        self.last_update = 0
        self.running = True

    def _add_headline(self, article, start_x=None, lane=None):
        """Find a lane and add a headline."""
        if lane is None:
            lane = random.randint(0, LANES - 1)
        y_pos = 10 + (lane * LANE_HEIGHT)

        if start_x is None:
            start_x = max(
                self.screen.get_width(),
                self.lane_last_x[lane] + random.randint(150, 400),
            )

        # Create headline without icon first
        h = Headline(article, self.font, self.small_font, start_x, y_pos, None)
        self.headlines.append(h)
        self.lane_last_x[lane] = start_x + h.width

        # Load icon in background to prevent stuttering
        def load_icon_bg(headline_obj, art_url):
            icon = self.fetcher.get_favicon(art_url)
            if icon:
                icon = pygame.transform.scale(icon, (24, 24))
                headline_obj.icon = icon
                headline_obj.text_offset = 32
                headline_obj.width += 32
                # Update rect width for hover detection
                headline_obj.rect.width = headline_obj.width

        Thread(
            target=load_icon_bg, args=(h, article.get("url", "")), daemon=True
        ).start()

    def update_headlines_loop(self):
        """Fetch fresh headlines every hour."""
        while self.running:
            now = time.time()
            if now - self.last_update >= UPDATE_INTERVAL:
                try:
                    articles = self.fetcher.fetch_headlines(cache=False)
                    for art in articles:
                        self._add_headline(art)
                    self.last_update = now
                except Exception as e:
                    print(f"Error updating: {e}")
            time.sleep(60)

    def run(self, initial_articles):
        # Initial distribution - spread them out across the entire screen and beyond
        total_width = self.screen.get_width()

        # Reset lane tracking for initial positioning
        self.lane_last_x = [-9999.0] * LANES

        for i, art in enumerate(initial_articles):
            lane = i % LANES

            # Distribute starting points sequentially within each lane
            # Use self.lane_last_x to ensure no overlap even at start
            start_x = max(0, self.lane_last_x[lane] + random.randint(200, 500))
            if i < LANES:  # First one in each lane starts closer to left
                start_x = random.randint(0, 300)

            self._add_headline(art, start_x=start_x, lane=lane)

        self.last_update = time.time()
        Thread(target=self.update_headlines_loop, daemon=True).start()

        ticker_speed_pps = 120  # Pixels per second

        while self.running:
            # Calculate delta time for smooth movement
            dt = self.clock.tick(FPS) / 1000.0  # Seconds since last frame
            mouse_pos = pygame.mouse.get_pos()
            # Check if any headline is hovered to pause scrolling
            hovered_headline = None
            for h in self.headlines:
                if h.rect.collidepoint(mouse_pos):
                    hovered_headline = h
                    break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if hovered_headline:
                            webbrowser.open(hovered_headline.url)
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h), pygame.RESIZABLE
                    )

            # Update and maintain lane state
            new_lane_last_x = [-9999.0] * LANES
            for h in self.headlines[:]:
                if not hovered_headline:
                    h.update(ticker_speed_pps * dt)

                lane = (int(h.y) - 10) // LANE_HEIGHT
                if 0 <= lane < LANES:
                    new_lane_last_x[lane] = max(new_lane_last_x[lane], h.x + h.width)

                if h.x + h.width < -200:
                    self.headlines.remove(h)
            self.lane_last_x = new_lane_last_x

            # Draw
            self.screen.fill(BG_COLOR)
            for h in self.headlines:
                if h.x < self.screen.get_width() and h.x + h.width > 0:
                    # Hover detection already done above
                    h.draw(self.screen, mouse_pos, self.small_font)

            # Draw tooltip last so it's on top
            if hovered_headline:
                hovered_headline.draw_tooltip(self.screen, mouse_pos, self.small_font)

            pygame.display.flip()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Scrolling News Ticker")
    parser.add_argument("--api-key", help="NewsAPI key")
    parser.add_argument("--country", help="Country")
    parser.add_argument("--category", help="Category")
    parser.add_argument("--sources", help="Sources")
    parser.add_argument("--q", help="Search")
    parser.add_argument("--pageSize", type=int, default=100)
    parser.add_argument("--page", type=int)
    parser.add_argument("--check-params", action="store_true")

    args = parser.parse_args()
    api_key = get_api_key(args.api_key)
    if not api_key:
        print("Error: NewsAPI key not found.")
        sys.exit(1)

    api_params = {
        k: v
        for k, v in vars(args).items()
        if v is not None and k not in ["api_key", "check_params"]
    }
    if not any(k in api_params for k in ["country", "category", "sources", "q"]):
        api_params["country"] = "us"

    fetcher = NewsFetcher(api_key, params_override=api_params)
    if args.check_params:
        opts = fetcher.get_valid_options()
        print(f"Countries: {opts['countries']}\nCategories: {opts['categories']}")
        sys.exit(0)

    try:
        articles = fetcher.fetch_headlines(cache=True)
    except Exception as e:
        print(f"Fetch error: {e}")
        sys.exit(1)

    NewsTickerApp(fetcher).run(articles)


if __name__ == "__main__":
    main()
