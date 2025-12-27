import os
import sys
import json
import time
import argparse
import webbrowser
import warnings
import random
import queue
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
CACHE_BASE_NAME = "headlines_cached"
API_KEY_FILE = "newsapikey.txt"
ICON_DIR = "icons"
UPDATE_CHECK_INTERVAL = 30  # Check for slot updates every 30 seconds
BG_COLOR = (10, 10, 15)
TEXT_COLOR = (240, 240, 240)
HOVER_COLOR = (0, 191, 255)
INFO_COLOR = (180, 180, 180)
TOOLTIP_BG = (30, 31, 40, 230)
NOTIFICATION_BG = (220, 50, 50, 200)
FONT_SIZE = 24
TICKER_SPEED_PPS = 120
FPS = 60
LANES = 5
LANE_HEIGHT = 80
CONTROLS_HEIGHT = 200
SCREEN_HEIGHT = LANES * LANE_HEIGHT + CONTROLS_HEIGHT + 40

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
        self.source_name = data.get("source", {}).get("name", "Unknown")

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
            except (ValueError, TypeError):
                # Ignore articles with malformed date strings.
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

    def _get_current_cache_filename(self):
        """Generates a cache filename based on the current 15-minute slot."""
        now = datetime.now()
        slot = (now.minute // 15) * 15
        date_str = now.strftime("%Y%m%d")
        return f"{CACHE_BASE_NAME}_{date_str}_{now.hour:02d}{slot:02d}.json"

    def fetch_headlines(self, cache=True):
        """Fetch news from API or local slot-based json cache."""
        cache_file = self._get_current_cache_filename()

        if cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"Warning: Could not read cache file '{cache_file}': {e}",
                    file=sys.stderr,
                )

        url = "https://newsapi.org/v2/top-headlines"
        response = requests.get(url, params=self.params)
        response.raise_for_status()
        articles = response.json().get("articles", [])

        if cache:
            # Clean up old caches from previous slots
            if os.path.exists("."):
                for f in os.listdir("."):
                    if f.startswith(CACHE_BASE_NAME) and f.endswith(".json"):
                        try:
                            os.remove(f)
                        except OSError:
                            pass

            with open(cache_file, "w") as f:
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
            except pygame.error as e:
                print(
                    f"Warning: could not load cached icon {icon_path}: {e}",
                    file=sys.stderr,
                )
                pass

        # Try Google's favicon service
        try:
            fav_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
            resp = requests.get(fav_url, timeout=5)
            if resp.status_code == 200:
                with open(icon_path, "wb") as f:
                    f.write(resp.content)
                return pygame.image.load(BytesIO(resp.content))
        except requests.exceptions.RequestException as e:
            print(
                f"Warning: could not fetch favicon for {domain}: {e}", file=sys.stderr
            )
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
        self.icon_queue = queue.Queue()
        self.last_update_slot = -1
        self.running = True
        self.current_articles = []

        # Filtering
        self.all_sources = {}  # name -> bool (selected)

        # Visuals
        self.notification = None  # (text, expiry_time, alpha)
        self.fade_alpha = 0  # for full screen fade
        self.is_fading_out = False
        self.next_batch = None

    def _add_headline(self, article, start_x=None, lane=None):
        """Find a lane and add a headline, ensuring no duplicates on screen."""
        url = article.get("url", "")
        if any(h.url == url for h in self.headlines):
            return False

        if lane is None:
            lane = random.randint(0, LANES - 1)
        y_pos = 10 + (lane * LANE_HEIGHT)

        if start_x is None:
            start_x = max(
                self.screen.get_width(),
                self.lane_last_x[lane] + random.randint(150, 400),
            )

        h = Headline(article, self.font, self.small_font, start_x, y_pos, None)

        # Pre-allocate space for the icon (32px) to prevent horizontal overlap when it loads
        h.width += 32
        h.rect.width = h.width

        # Don't add if the source is unselected and it would start off-screen
        is_selected = self.all_sources.get(h.source_name, True)
        if start_x > self.screen.get_width() and not is_selected:
            return False

        self.headlines.append(h)
        self.lane_last_x[lane] = start_x + h.width

        # Load icon in background to prevent stuttering
        def load_icon_bg(headline_obj, art_url):
            icon = self.fetcher.get_favicon(art_url)
            if icon:
                self.icon_queue.put((headline_obj, icon))

        Thread(
            target=load_icon_bg, args=(h, article.get("url", "")), daemon=True
        ).start()
        return True

    def update_headlines_loop(self):
        """Checks for new headlines in 15-minute intervals."""
        while self.running:
            now = datetime.now()
            current_slot = (now.minute // 15) * 15

            # Check if we moved to a new slot or haven't checked yet
            if self.last_update_slot != current_slot:
                try:
                    articles = self.fetcher.fetch_headlines(cache=True)
                    self.next_batch = articles
                    self.is_fading_out = True  # Trigger transition
                    self.last_update_slot = current_slot
                except Exception as e:
                    self.notification = [
                        "Update Failed. Retrying in 15m...",
                        time.time() + 5,
                        255,
                    ]
                    print(f"Update failed: {e}")
                    self.last_update_slot = current_slot
            time.sleep(UPDATE_CHECK_INTERVAL)

    def _sync_sources(self, articles):
        """Update the source list from fetched articles."""
        new_sources = {}
        for art in articles:
            name = art.get("source", {}).get("name", "Unknown")
            new_sources[name] = self.all_sources.get(name, True)
        self.all_sources = new_sources
        self.current_articles = articles

    def _draw_controls(self, mouse_pos):
        """Draw source filters distributed evenly across columns."""
        start_y = LANES * LANE_HEIGHT + 20
        pygame.draw.line(
            self.screen,
            (50, 50, 70),
            (0, start_y),
            (self.screen.get_width(), start_y),
            2,
        )

        x_base, y_base = 20, start_y + 20
        col_width = 220
        lh = 25
        self.source_rects = {}

        sorted_sources = sorted(self.all_sources.keys())
        num_sources = len(sorted_sources)
        if num_sources == 0:
            return

        # Calculate layout to be as even as possible
        max_rows = CONTROLS_HEIGHT // lh
        num_cols = max(1, (self.screen.get_width() - 40) // col_width)

        # Determine actual items per column to fill all available columns if possible
        items_per_col = (num_sources + num_cols - 1) // num_cols
        # But don't exceed what fits vertically
        items_per_col = max(1, min(items_per_col, max_rows))

        for i, name in enumerate(sorted_sources):
            col = i // items_per_col
            row = i % items_per_col

            x = x_base + col * col_width
            y = y_base + row * lh

            if x > self.screen.get_width() - 100 or y > SCREEN_HEIGHT - 20:
                continue

            is_selected = self.all_sources[name]
            rect = pygame.Rect(x, y, 16, 16)

            pygame.draw.rect(self.screen, (100, 100, 130), rect, 1)
            if is_selected:
                pygame.draw.rect(self.screen, HOVER_COLOR, rect.inflate(-6, -6))

            color = TEXT_COLOR if is_selected else INFO_COLOR
            ts = self.small_font.render(name, True, color)
            self.screen.blit(ts, (x + 25, y - 2))

            self.source_rects[name] = pygame.Rect(x, y, col_width, lh)

    def _draw_notification(self):
        """Draw fading notification on update failure."""
        if self.notification:
            text, expiry, alpha = self.notification
            now = time.time()
            if now > expiry:
                self.notification[2] -= 5
                if self.notification[2] <= 0:
                    self.notification = None
                    return

            tw, th = self.small_font.size(text)
            rect = pygame.Rect(
                self.screen.get_width() // 2 - tw // 2 - 10, 10, tw + 20, th + 10
            )
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            color = list(NOTIFICATION_BG)
            color[3] = self.notification[2]
            s.fill(color)
            self.screen.blit(s, (rect.x, rect.y))

            t_color = list(TEXT_COLOR)
            t_color = (t_color[0], t_color[1], t_color[2], self.notification[2])
            ts = self.small_font.render(text, True, t_color)
            self.screen.blit(ts, (rect.x + 10, rect.y + 5))

    def run(self, initial_articles):
        # Initial setup
        self._sync_sources(initial_articles)
        self.lane_last_x = [0.0] * LANES
        self.source_rects = {}

        # Initial articles spread across lanes and screen
        for i, art in enumerate(initial_articles):
            lane = i % LANES
            # For the very first items in each lane, start somewhat randomly on screen
            if i < LANES:
                start_x = random.randint(0, 400)
            else:
                # Flow naturally from the last item added
                start_x = self.lane_last_x[lane] + random.randint(200, 500)

            self._add_headline(art, start_x=start_x, lane=lane)

        now = datetime.now()
        self.last_update_slot = (now.minute // 15) * 15
        Thread(target=self.update_headlines_loop, daemon=True).start()

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            # Process background loaded icons
            while not self.icon_queue.empty():
                try:
                    h_obj, icon_surf = self.icon_queue.get_nowait()
                    h_obj.icon = pygame.transform.scale(icon_surf, (24, 24))
                    h_obj.text_offset = 32
                    # width was already pre-allocated in _add_headline
                except queue.Empty:
                    break

            mouse_pos = pygame.mouse.get_pos()
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
                        for name, rect in self.source_rects.items():
                            if rect.collidepoint(mouse_pos):
                                self.all_sources[name] = not self.all_sources[name]
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h), pygame.RESIZABLE
                    )

            # Update and transition logic
            if self.is_fading_out:
                self.fade_alpha = min(255, self.fade_alpha + 15)
                if self.fade_alpha >= 255:
                    self.headlines = []
                    self.lane_last_x = [float(self.screen.get_width())] * LANES
                    self._sync_sources(self.next_batch)
                    for i, art in enumerate(self.next_batch):
                        lane = i % LANES
                        # Let _add_headline calculate the positions based on lane_last_x
                        self._add_headline(art, lane=lane)
                    self.is_fading_out = False
            else:
                self.fade_alpha = max(0, self.fade_alpha - 5)

            # Update lane state
            new_lane_last_x = [-9999.0] * LANES
            for h in self.headlines[:]:
                if not hovered_headline:
                    h.update(TICKER_SPEED_PPS * dt)

                lane = (int(h.y) - 10) // LANE_HEIGHT
                if 0 <= lane < LANES:
                    new_lane_last_x[lane] = max(new_lane_last_x[lane], h.x + h.width)

                if h.x + h.width < -200:
                    old_lane = (int(h.y) - 10) // LANE_HEIGHT
                    self.headlines.remove(h)

                    # Recycle: Pick a new headline for this lane from active sources
                    # Filter out anything already on screen
                    current_urls = {h.url for h in self.headlines}
                    available_articles = [
                        a
                        for a in self.current_articles
                        if self.all_sources.get(
                            a.get("source", {}).get("name", "Unknown"), True
                        )
                        and a.get("url") not in current_urls
                    ]

                    if available_articles:
                        self._add_headline(
                            random.choice(available_articles), lane=old_lane
                        )

            # CRITICAL: Recalculate lane_last_x after all updates/additions
            self.lane_last_x = [-9999.0] * LANES
            for h in self.headlines:
                lane = (int(h.y) - 10) // LANE_HEIGHT
                if 0 <= lane < LANES:
                    self.lane_last_x[lane] = max(self.lane_last_x[lane], h.x + h.width)

            # Draw
            self.screen.fill(BG_COLOR)
            for h in self.headlines:
                if h.x < self.screen.get_width() and h.x + h.width > 0:
                    h.draw(self.screen, mouse_pos, self.small_font)

            if hovered_headline:
                hovered_headline.draw_tooltip(self.screen, mouse_pos, self.small_font)

            self._draw_controls(mouse_pos)
            self._draw_notification()

            if self.fade_alpha > 0:
                overlay = pygame.Surface(
                    (self.screen.get_width(), self.screen.get_height())
                )
                overlay.fill((0, 0, 0))
                overlay.set_alpha(self.fade_alpha)
                self.screen.blit(overlay, (0, 0))

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
        print("Error: NewsAPI key not found.", file=sys.stderr)
        sys.exit(1)

    api_params = {}
    forbidden_keys = ["api_key", "check_params"]
    for key, value in vars(args).items():
        if value is not None and key not in forbidden_keys:
            api_params[key] = value

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
