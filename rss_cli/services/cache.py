"""Cache layer for fetched articles — stores at ~/.cache/rss-cli/."""

from __future__ import annotations

import json
import sqlite3
import time

from rss_cli.models.article import Article, Feed
from rss_cli.services.config import (
    bookmarks_path,
    cache_file_path,
    get_config,
    read_state_path,
)

# --- Article cache (SQLite) ---


def _row_to_article(row: sqlite3.Row) -> Article:
    """Convert a database row to an Article instance."""
    tags: list[str] = json.loads(row["tags"])
    return Article(
        title=row["title"],
        link=row["link"],
        description=row["description"],
        content=row["content"],
        author=row["author"],
        pub_date=row["pub_date"],
        tags=tags,
        feed_title=row["feed_title"],
        feed_url=row["feed_url"],
    )


def _get_db(db_path: object) -> sqlite3.Connection:
    """Open the cache database and ensure the schema exists."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cache_meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS articles (
            link       TEXT PRIMARY KEY,
            title      TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            content    TEXT NOT NULL DEFAULT '',
            author     TEXT NOT NULL DEFAULT '',
            pub_date   TEXT NOT NULL DEFAULT '',
            tags       TEXT NOT NULL DEFAULT '[]',
            feed_title TEXT NOT NULL DEFAULT '',
            feed_url   TEXT NOT NULL DEFAULT ''
        );
    """)
    conn.commit()
    return conn


def save_cache(articles: list[Article]) -> None:
    """Persist articles to the SQLite cache."""
    path = cache_file_path()
    conn = _get_db(path)
    try:
        conn.execute("DELETE FROM articles")
        conn.execute(
            "INSERT OR REPLACE INTO cache_meta (key, value) VALUES (?, ?)",
            ("cached_at", str(time.time())),
        )
        conn.executemany(
            """INSERT OR REPLACE INTO articles
               (link, title, description, content, author, pub_date, tags, feed_title, feed_url)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    a.link,
                    a.title,
                    a.description,
                    a.content,
                    a.author,
                    a.pub_date,
                    json.dumps(a.tags, ensure_ascii=False),
                    a.feed_title,
                    a.feed_url,
                )
                for a in articles
            ],
        )
        conn.commit()
    finally:
        conn.close()


def load_cache() -> list[Article] | None:
    """Load articles from the SQLite cache. Returns None if expired or missing."""
    path = cache_file_path()
    if not path.exists():
        return None

    conn = _get_db(path)
    try:
        # Check TTL
        row = conn.execute(
            "SELECT value FROM cache_meta WHERE key = ?", ("cached_at",)
        ).fetchone()
        if row is None:
            return None
        cached_at = float(row["value"])
        ttl = get_config().cache_ttl_seconds
        if time.time() - cached_at > ttl:
            return None

        rows = conn.execute(
            """SELECT link, title, description, content, author, pub_date, tags,
                      feed_title, feed_url
               FROM articles"""
        ).fetchall()
        return [_row_to_article(r) for r in rows]
    except (sqlite3.Error, ValueError, OSError):
        return None
    finally:
        conn.close()


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

_read_state: set[str] | None = None


def _get_read_state() -> set[str]:
    """Return the in-memory read state, loading from disk on first call."""
    global _read_state
    if _read_state is None:
        path = read_state_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                _read_state = set(data.get("read", []))
            except (json.JSONDecodeError, OSError):
                _read_state = set()
        else:
            _read_state = set()
    return _read_state


def _flush_read_state() -> None:
    """Write the in-memory read state to disk."""
    global _read_state
    if _read_state is None:
        return
    path = read_state_path()
    data = {"read": list(_read_state)}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_read_state() -> set[str]:
    """Public API: return a copy of the current read state."""
    return set(_get_read_state())


def save_read_state(read_links: set[str]) -> None:
    """Public API: replace read state and flush to disk."""
    global _read_state
    _read_state = set(read_links)
    _flush_read_state()


def mark_article_read(link: str) -> None:
    state = _get_read_state()
    state.add(link)
    _flush_read_state()


def apply_read_state(articles: list[Article]) -> list[Article]:
    state = _get_read_state()
    for article in articles:
        article.is_read = article.link in state
    return articles


# --- Bookmarks ---

_bookmark_state: set[str] | None = None


def _get_bookmark_state() -> set[str]:
    """Return the in-memory bookmark state, loading from disk on first call."""
    global _bookmark_state
    if _bookmark_state is None:
        path = bookmarks_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                _bookmark_state = set(data.get("bookmarks", []))
            except (json.JSONDecodeError, OSError):
                _bookmark_state = set()
        else:
            _bookmark_state = set()
    return _bookmark_state


def _flush_bookmark_state() -> None:
    """Write the in-memory bookmark state to disk."""
    global _bookmark_state
    if _bookmark_state is None:
        return
    path = bookmarks_path()
    data = {"bookmarks": list(_bookmark_state)}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_bookmarks() -> set[str]:
    """Public API: return a copy of the current bookmark state."""
    return set(_get_bookmark_state())


def save_bookmarks(bookmark_links: set[str]) -> None:
    """Public API: replace bookmark state and flush to disk."""
    global _bookmark_state
    _bookmark_state = set(bookmark_links)
    _flush_bookmark_state()


def toggle_bookmark(link: str) -> bool:
    """Toggle bookmark for an article link. Returns True if now bookmarked."""
    state = _get_bookmark_state()
    if link in state:
        state.discard(link)
        _flush_bookmark_state()
        return False
    else:
        state.add(link)
        _flush_bookmark_state()
        return True


def apply_bookmark_state(articles: list[Article]) -> list[Article]:
    state = _get_bookmark_state()
    for article in articles:
        article.is_bookmarked = article.link in state
    return articles


def apply_all_state(articles: list[Article]) -> list[Article]:
    """Apply both read and bookmark state to articles."""
    read_state = _get_read_state()
    bookmark_state = _get_bookmark_state()
    for article in articles:
        article.is_read = article.link in read_state
        article.is_bookmarked = article.link in bookmark_state
    return articles


def invalidate_state_cache() -> None:
    """Force reload from disk on next access. Call after external state changes."""
    global _read_state, _bookmark_state
    _read_state = None
    _bookmark_state = None
