"""Data models for RSS feeds and articles."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse


def _parse_date(date_str: str | None) -> datetime:
    if not date_str:
        return datetime.min

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
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return datetime.min


def _format_date(date_str: str | None) -> str:
    dt = _parse_date(date_str)
    if dt == datetime.min:
        return "Unknown"
    return dt.strftime("%Y-%m-%d %H:%M")


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

    @property
    def pub_date_parsed(self) -> datetime:
        return _parse_date(self.pub_date)

    @property
    def pub_date_display(self) -> str:
        return _format_date(self.pub_date)

    @property
    def feed_name(self) -> str:
        """Short identifier extracted from the feed URL (e.g. 'ycombinator')."""
        parsed = urlparse(self.feed_url)
        host = parsed.hostname or ""
        parts = host.split(".")
        # Skip common prefixes like 'www', 'news', 'rss', 'feed', 'blog'
        skip = {"www", "news", "rss", "feed", "blog", "feeds", "api"}
        name_parts = [p for p in parts if p.lower() not in skip]
        return name_parts[0] if name_parts else parts[-2] if len(parts) >= 2 else host

    @property
    def short_description(self) -> str:
        clean = self.description.replace("\n", " ").strip()
        return _truncate(clean, 120)

    @property
    def status_icon(self) -> str:
        """Return a combined status icon: read/unread + bookmarked."""
        parts: list[str] = []
        parts.append("★" if self.is_bookmarked else "☆")
        parts.append("○" if self.is_read else "●")
        return " ".join(parts)

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
