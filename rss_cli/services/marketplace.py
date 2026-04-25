"""Marketplace — live RSS feed discovery via Feedly Search API.

Uses https://cloud.feedly.com/v3/search/feeds to find RSS feeds.
No API key required — free and unlimited.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

# Feedly's public feed search endpoint — no auth needed.
_FEEDLY_SEARCH_URL = "https://cloud.feedly.com/v3/search/feeds"


@dataclass
class MarketplaceFeed:
    """A feed discovered through the marketplace."""

    title: str
    url: str
    description: str = ""
    website: str = ""
    language: str = ""
    subscribers: int = 0


@dataclass
class MarketplaceCategory:
    """A category that triggers a Feedly search query."""

    name: str
    emoji: str
    query: str  # search term sent to Feedly API


# Curated categories with their Feedly search queries
CATEGORIES: list[MarketplaceCategory] = [
    MarketplaceCategory("Tech", "💻", "technology news"),
    MarketplaceCategory("Programming", "⌨️", "programming blog"),
    MarketplaceCategory("Science", "🔬", "science research"),
    MarketplaceCategory("AI & ML", "🤖", "artificial intelligence machine learning"),
    MarketplaceCategory("Design", "🎨", "design ux ui"),
    MarketplaceCategory("Business", "📊", "business finance"),
    MarketplaceCategory("News", "📰", "world news"),
    MarketplaceCategory("Gaming", "🎮", "gaming news"),
    MarketplaceCategory("DevOps", "🔧", "devops cloud infrastructure"),
    MarketplaceCategory("Security", "🔒", "cybersecurity infosec"),
    MarketplaceCategory("Productivity", "⚡", "productivity self-improvement"),
    MarketplaceCategory("Startups", "🚀", "startups entrepreneurship"),
    MarketplaceCategory("Crypto", "🪙", "cryptocurrency blockchain web3"),
    MarketplaceCategory("Open Source", "🐧", "open source linux"),
]


def _feedly_result_to_feed(item: dict[str, object]) -> MarketplaceFeed | None:
    """Convert a Feedly search result item to a MarketplaceFeed."""
    feed_id = str(item.get("id", ""))
    # Feedly feed IDs look like "feed/http://..." or "feed/https://..."
    url = feed_id.removeprefix("feed/")
    if not url.startswith(("http://", "https://")):
        return None

    title = str(item.get("title", "")) or str(item.get("websiteTitle", url))
    description = str(item.get("description", ""))
    website = str(item.get("website", ""))
    language = str(item.get("language", ""))
    subscribers = int(str(item.get("subscribers", "0")))

    return MarketplaceFeed(
        title=title,
        url=url,
        description=description,
        website=website,
        language=language,
        subscribers=subscribers,
    )


async def search_feeds(query: str, limit: int = 20) -> list[MarketplaceFeed]:
    """Search for RSS feeds using the Feedly API. Returns results sorted by subscribers."""
    if not query.strip():
        return []

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(
                _FEEDLY_SEARCH_URL,
                params={"query": query, "count": limit},
            )
            response.raise_for_status()
    except httpx.HTTPError:
        return []

    data = response.json()
    results: list[MarketplaceFeed] = []

    for item in data.get("results", []):
        feed = _feedly_result_to_feed(item)
        if feed is not None:
            results.append(feed)

    # Sort by subscriber count (most popular first)
    results.sort(key=lambda f: f.subscribers, reverse=True)
    return results


async def search_category(category: MarketplaceCategory, limit: int = 20) -> list[MarketplaceFeed]:
    """Search for feeds within a category."""
    return await search_feeds(category.query, limit=limit)


def search_feeds_sync(query: str, limit: int = 20) -> list[MarketplaceFeed]:
    """Synchronous wrapper for search_feeds."""
    return asyncio.run(search_feeds(query, limit=limit))


def get_subscribed_urls() -> set[str]:
    """Return the set of currently subscribed feed URLs."""
    from rss_cli.services.config import load_feed_urls

    return set(load_feed_urls())
