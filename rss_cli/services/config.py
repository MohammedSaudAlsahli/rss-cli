"""Configuration management — XDG-compliant paths."""

from __future__ import annotations

import tomllib
from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir, user_data_dir

APP_NAME = "rss-cli"
CONFIG_FILE = "config.toml"
FEEDS_FILE = "feeds.txt"
CACHE_FILE = "articles.json"
READ_STATE_FILE = "read_state.json"
BOOKMARKS_FILE = "bookmarks.json"


def config_dir() -> Path:
    """Return the XDG config directory for rss-cli."""
    path = Path(user_config_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    """Return the XDG cache directory for rss-cli."""
    path = Path(user_cache_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    """Return the XDG data directory for rss-cli."""
    path = Path(user_data_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


def feeds_file_path() -> Path:
    """Return path to the feeds list file."""
    return config_dir() / FEEDS_FILE


def cache_file_path() -> Path:
    """Return path to the articles cache file."""
    return cache_dir() / CACHE_FILE


def read_state_path() -> Path:
    """Return path to the read state file."""
    return data_dir() / READ_STATE_FILE


def bookmarks_path() -> Path:
    """Return path to the bookmarks file."""
    return data_dir() / BOOKMARKS_FILE


def config_file_path() -> Path:
    """Return path to the config TOML file."""
    return config_dir() / CONFIG_FILE


class Config:
    """Application configuration loaded from TOML."""

    def __init__(self) -> None:
        self.cache_ttl_seconds: int = 300  # 5 minutes default
        self.max_articles_per_feed: int = 50
        self._load()

    def _load(self) -> None:
        """Load config from TOML file if it exists."""
        path = config_file_path()
        if not path.exists():
            return
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            settings = data.get("settings", {})
            self.cache_ttl_seconds = settings.get(
                "cache_ttl_seconds", self.cache_ttl_seconds
            )
            self.max_articles_per_feed = settings.get(
                "max_articles_per_feed", self.max_articles_per_feed
            )
        except (tomllib.TOMLDecodeError, OSError):
            pass  # Use defaults on error


# Module-level singleton — lazy loaded
_config: Config | None = None


def get_config() -> Config:
    """Get the application config singleton."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def load_feed_urls() -> list[str]:
    """Load feed URLs from the feeds file."""
    path = feeds_file_path()
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def save_feed_url(url: str) -> bool:
    """Add a feed URL. Returns True if added, False if already exists."""
    urls = load_feed_urls()
    if url in urls:
        return False
    path = feeds_file_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{url}\n")
    return True


def remove_feed_url(url: str) -> bool:
    """Remove a feed URL. Returns True if removed, False if not found."""
    urls = load_feed_urls()
    if url not in urls:
        return False
    path = feeds_file_path()
    remaining = [u for u in urls if u != url]
    path.write_text("\n".join(remaining) + "\n" if remaining else "", encoding="utf-8")
    return True
