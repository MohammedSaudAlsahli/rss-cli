"""Data models for RSS feeds and articles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from functools import cached_property
from urllib.parse import urlparse


class FeedType(Enum):
    """Source type of a feed."""

    RSS = "rss"
    REDDIT = "reddit"
    TWITTER = "twitter"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        return self.value.capitalize()


def detect_feed_type(url: str) -> FeedType:
    """Detect the source type from a feed URL."""
    parsed = urlparse(url)
    host = parsed.hostname or ""

    if "reddit.com" in host:
        return FeedType.REDDIT

    if host in _get_nitter_instances() and parsed.path.endswith("/rss"):
        return FeedType.TWITTER

    return FeedType.RSS


def _get_nitter_instances() -> list[str]:
    """Lazy import to avoid circular dependency."""
    from rss_cli.services.config import get_nitter_instances

    return get_nitter_instances()


def _parse_date(date_str: str | None) -> datetime:
    """Parse a date string, always returning a UTC-aware datetime."""
    if not date_str:
        return datetime.min.replace(tzinfo=UTC)

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            # Make naive datetimes UTC-aware so all are comparable
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except (ValueError, AttributeError):
            continue
    return datetime.min.replace(tzinfo=UTC)


def _format_date(date_str: str | None) -> str:
    dt = _parse_date(date_str)
    if dt == datetime.min.replace(tzinfo=UTC):
        return "Unknown"
    return dt.strftime("%d/%m %H:%M")


def _truncate(text: str, max_len: int = 120) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


@dataclass
class Article:
    """A single RSS article entry."""

    title: str
    link: str
    description: str
    content: str
    author: str
    pub_date: str
    tags: list[str]
    feed_title: str
    feed_url: str
    is_read: bool = False
    is_bookmarked: bool = False

    @cached_property
    def pub_date_parsed(self) -> datetime:
        return _parse_date(self.pub_date)

    @cached_property
    def pub_date_display(self) -> str:
        return _format_date(self.pub_date)

    @cached_property
    def feed_type(self) -> FeedType:
        """Detect the source type from the feed URL. Cached."""
        return detect_feed_type(self.feed_url)

    @cached_property
    def feed_name(self) -> str:
        """Short identifier from feed URL (e.g. 'ycombinator', 'r/python', '@user'). Cached."""
        parsed = urlparse(self.feed_url)
        host = parsed.hostname or ""
        path = parsed.path.rstrip("/")

        # Reddit: /r/{subreddit}/... → r/subreddit
        if "reddit.com" in host:
            import re

            match = re.match(r"/r/([^/]+)", path)
            if match:
                return f"r/{match.group(1)}"

        # Nitter: /{username}/rss → @username (only for known Nitter instances)
        if path.endswith("/rss"):
            from rss_cli.services.config import get_nitter_instances

            if host in get_nitter_instances():
                parts = path.rsplit("/", 2)
                if len(parts) >= 2 and parts[-2]:
                    return f"@{parts[-2]}"

        # Default: hostname-based extraction
        parts = host.split(".")
        skip = {"www", "news", "rss", "feed", "blog", "feeds", "api"}
        name_parts = [p for p in parts if p.lower() not in skip]
        return name_parts[0] if name_parts else parts[-2] if len(parts) >= 2 else host

    @cached_property
    def parsed_content(self) -> str:
        """HTML-stripped content, cached after first call."""
        from rss_cli.markup import html_to_text

        if self.content and len(self.content) > len(self.description):
            cleaned = html_to_text(self.content)
            if cleaned.strip().lower() not in {"[comments]", "comments", ""}:
                return cleaned
        if self.description:
            cleaned = html_to_text(self.description)
            if cleaned.strip().lower() not in {"[comments]", "comments", ""}:
                return cleaned
        return ""

    @property
    def short_description(self) -> str:
        clean = self.description.replace("\n", " ").strip()
        return _truncate(clean, 120)

    @classmethod
    def from_feedparser_entry(cls, entry: object, feed_title: str, feed_url: str) -> Article:
        e = entry

        title = getattr(e, "title", "Untitled")
        link = ""
        if hasattr(e, "link") and e.link:
            link = e.link
        elif hasattr(e, "links") and e.links:
            link = e.links[0].get("href", "")

        description = getattr(e, "description", "")
        if not description:
            description = getattr(e, "summary", "")

        content = ""
        if hasattr(e, "content") and e.content:
            content = e.content[0].get("value", "")
        if not content:
            content = description

        author = getattr(e, "author", "")
        if not author:
            author = getattr(e, "dc_creator", "")

        pub_date = getattr(e, "published", "")
        if not pub_date:
            pub_date = getattr(e, "updated", "")

        tags: list[str] = []
        if hasattr(e, "tags") and e.tags:
            tags = [t.term for t in e.tags if hasattr(t, "term")]

        return cls(
            title=title,
            link=link,
            description=description,
            content=content,
            author=author,
            pub_date=pub_date,
            tags=tags,
            feed_title=feed_title,
            feed_url=feed_url,
        )


@dataclass
class Feed:
    """An RSS feed subscription."""

    url: str
    title: str = ""
    articles: list[Article] = field(default_factory=list)

    @property
    def article_count(self) -> int:
        return len(self.articles)

    @property
    def last_updated(self) -> str:
        if not self.articles:
            return "Never"
        latest = max(self.articles, key=lambda a: a.pub_date_parsed)
        return latest.pub_date_display
