"""Services for RSS feed management."""

from rss_cli.services.cache import (
    apply_all_state,
    apply_bookmark_state,
    apply_read_state,
    load_bookmarks,
    load_cache,
    load_read_state,
    mark_article_read,
    save_bookmarks,
    save_cache,
    save_read_state,
    toggle_bookmark,
)
from rss_cli.services.config import (
    Config,
    get_config,
    load_feed_urls,
    remove_feed_url,
    save_feed_url,
)
from rss_cli.services.fetcher import fetch_feeds, fetch_feeds_sync

__all__ = [
    "Config",
    "get_config",
    "load_feed_urls",
    "save_feed_url",
    "remove_feed_url",
    "fetch_feeds",
    "fetch_feeds_sync",
    "load_cache",
    "save_cache",
    "load_read_state",
    "save_read_state",
    "mark_article_read",
    "apply_read_state",
    "load_bookmarks",
    "save_bookmarks",
    "toggle_bookmark",
    "apply_bookmark_state",
    "apply_all_state",
]
