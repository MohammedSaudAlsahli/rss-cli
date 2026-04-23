"""Cache layer for fetched articles — stores at ~/.cache/rss-cli/."""

from __future__ import annotations

import json
import time

from rss_cli.models.feed import Article, Feed
from rss_cli.services.config import (
    bookmarks_path,
    cache_file_path,
    get_config,
    read_state_path,
)


def _articles_to_dicts(articles: list[Article]) -> list[dict[str, object]]:
    return [
        {
            "title": a.title,
            "link": a.link,
            "description": a.description,
            "content": a.content,
            "author": a.author,
            "pub_date": a.pub_date,
            "tags": a.tags,
            "feed_title": a.feed_title,
            "feed_url": a.feed_url,
        }
        for a in articles
    ]


def _dicts_to_articles(dicts: list[dict[str, object]]) -> list[Article]:
    articles: list[Article] = []
    for d in dicts:
        articles.append(
            Article(
                title=str(d.get("title", "Untitled")),
                link=str(d.get("link", "")),
                description=str(d.get("description", "")),
                content=str(d.get("content", "")),
                author=str(d.get("author", "")),
                pub_date=str(d.get("pub_date", "")),
                tags=[str(t) for t in d.get("tags", [])],  # type: ignore[attr-defined]
                feed_title=str(d.get("feed_title", "")),
                feed_url=str(d.get("feed_url", "")),
            )
        )
    return articles


def save_cache(articles: list[Article]) -> None:
    path = cache_file_path()
    data = {
        "timestamp": time.time(),
        "articles": _articles_to_dicts(articles),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cache() -> list[Article] | None:
    path = cache_file_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    timestamp = data.get("timestamp", 0)
    ttl = get_config().cache_ttl_seconds
    if time.time() - timestamp > ttl:
        return None

    raw_articles = data.get("articles", [])
    return _dicts_to_articles(raw_articles)


def group_by_feed(articles: list[Article]) -> list[Feed]:
    feeds_map: dict[str, Feed] = {}
    for article in articles:
        if article.feed_url not in feeds_map:
            feeds_map[article.feed_url] = Feed(
                url=article.feed_url,
                title=article.feed_title or article.feed_url,
            )
        feeds_map[article.feed_url].articles.append(article)

    for feed in feeds_map.values():
        feed.articles.sort(key=lambda a: a.pub_date_parsed, reverse=True)

    return sorted(feeds_map.values(), key=lambda f: f.title.lower())


# --- Read state ---


def load_read_state() -> set[str]:
    path = read_state_path()
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("read", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_read_state(read_links: set[str]) -> None:
    path = read_state_path()
    data = {"read": list(read_links)}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_article_read(link: str) -> None:
    state = load_read_state()
    state.add(link)
    save_read_state(state)


def apply_read_state(articles: list[Article]) -> list[Article]:
    state = load_read_state()
    for article in articles:
        article.is_read = article.link in state
    return articles


# --- Bookmarks ---


def load_bookmarks() -> set[str]:
    path = bookmarks_path()
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return set(data.get("bookmarks", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_bookmarks(bookmark_links: set[str]) -> None:
    path = bookmarks_path()
    data = {"bookmarks": list(bookmark_links)}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def toggle_bookmark(link: str) -> bool:
    """Toggle bookmark for an article link. Returns True if now bookmarked."""
    state = load_bookmarks()
    if link in state:
        state.discard(link)
        save_bookmarks(state)
        return False
    else:
        state.add(link)
        save_bookmarks(state)
        return True


def apply_bookmark_state(articles: list[Article]) -> list[Article]:
    state = load_bookmarks()
    for article in articles:
        article.is_bookmarked = article.link in state
    return articles


def apply_all_state(articles: list[Article]) -> list[Article]:
    """Apply both read and bookmark state to articles."""
    read_state = load_read_state()
    bookmark_state = load_bookmarks()
    for article in articles:
        article.is_read = article.link in read_state
        article.is_bookmarked = article.link in bookmark_state
    return articles
