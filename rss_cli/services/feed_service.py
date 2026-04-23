"""Feed fetching and parsing service — fully async with parallel fetching."""

from __future__ import annotations

import asyncio

import feedparser  # type: ignore[import-untyped]
import httpx

from rss_cli.models.feed import Article, Feed
from rss_cli.services.cache import (
    apply_all_state,
    group_by_feed,
    load_cache,
    save_cache,
)
from rss_cli.services.config import get_config, load_feed_urls


async def _fetch_feed(client: httpx.AsyncClient, url: str) -> list[Article]:
    """Fetch and parse a single RSS feed asynchronously."""
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPError:
        return []

    feed = feedparser.parse(response.text)

    # feedparser sets bozo for parse errors — still usable for partial results
    feed_title_obj = getattr(feed, "channel", None)
    title = getattr(feed_title_obj, "title", url) if feed_title_obj else url

    articles: list[Article] = []
    entries = getattr(feed, "entries", [])
    max_articles = get_config().max_articles_per_feed

    for entry in entries[:max_articles]:
        article = Article.from_feedparser_entry(entry, title, url)
        articles.append(article)

    return articles


async def _fetch_all_feeds(urls: list[str]) -> list[Article]:
    """Fetch multiple feeds in parallel using async httpx."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(15.0),
        follow_redirects=True,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    ) as client:
        tasks = [_fetch_feed(client, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles: list[Article] = []
    for result in results:
        if isinstance(result, BaseException):
            continue  # Skip failed feeds silently
        all_articles.extend(list(result))

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

    all_articles = await _fetch_all_feeds(urls)

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
