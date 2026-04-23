"""Feed fetching and parsing service — async with parallel fetching."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import feedparser  # type: ignore[import-untyped]
import httpx

from rss_cli.models.feed import Article
from rss_cli.services.cache import (
    apply_all_state,
    group_by_feed,
    load_cache,
    save_cache,
)
from rss_cli.services.config import get_config, load_feed_urls

if TYPE_CHECKING:
    from rss_cli.models.feed import Feed


def _fetch_feed(url: str) -> list[Article]:
    """Fetch and parse a single RSS feed. Returns list of articles."""
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPError:
        return []

    feed = feedparser.parse(response.text)

    # feedparser sets bozo for parse errors — still usable for partial results
    feed_title = getattr(feed, "channel", None)
    title = getattr(feed_title, "title", url) if feed_title else url

    articles: list[Article] = []
    entries = getattr(feed, "entries", [])
    max_articles = get_config().max_articles_per_feed

    for entry in entries[:max_articles]:
        article = Article.from_feedparser_entry(entry, title, url)
        articles.append(article)

    return articles


def _fetch_all_sync(urls: list[str]) -> list[Article]:
    """Fetch multiple feeds in parallel using ThreadPoolExecutor."""
    all_articles: list[Article] = []

    with ThreadPoolExecutor(max_workers=min(len(urls), 10)) as executor:
        futures = {executor.submit(_fetch_feed, url): url for url in urls}
        for future in futures:
            try:
                articles = future.result(timeout=20)
                all_articles.extend(articles)
            except Exception:
                continue  # Skip failed feeds silently

    return all_articles


async def fetch_feeds(force: bool = False) -> list[Feed]:
    """Fetch all feeds and return Feed objects grouped by source.

    Uses cache if available and not expired.
    Set force=True to bypass cache and always fetch fresh.
    """
    # Check cache first (unless force refresh)
    if not force:
        cached = load_cache()
        if cached is not None:
            articles = apply_all_state(cached)
            return group_by_feed(articles)

    # Fetch fresh
    urls = load_feed_urls()
    if not urls:
        return []

    loop = asyncio.get_event_loop()
    all_articles = await loop.run_in_executor(None, _fetch_all_sync, urls)

    # Sort all articles by date (newest first)
    all_articles.sort(key=lambda a: a.pub_date_parsed, reverse=True)

    # Save to cache
    save_cache(all_articles)

    # Apply read + bookmark state
    all_articles = apply_all_state(all_articles)

    return group_by_feed(all_articles)


def fetch_feeds_sync(force: bool = False) -> list[Feed]:
    """Synchronous wrapper for fetch_feeds."""
    return asyncio.run(fetch_feeds(force=force))
