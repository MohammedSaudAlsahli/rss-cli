"""Tests for cache service."""

import json
from pathlib import Path
from unittest.mock import patch

from rss_cli.models.article import Article
from rss_cli.services.cache import (
    apply_all_state,
    apply_bookmark_state,
    apply_read_state,
    group_by_feed,
    invalidate_state_cache,
    load_cache,
    load_read_state,
    mark_article_read,
    save_cache,
    toggle_bookmark,
)


def _make_article(
    title: str = "Test",
    link: str = "https://example.com/a1",
    feed_title: str = "Test Feed",
    feed_url: str = "https://example.com/feed",
) -> Article:
    return Article(
        title=title,
        link=link,
        description="Desc",
        content="Content",
        author="Author",
        pub_date="Mon, 23 Apr 2026 10:00:00 +0000",
        tags=[],
        feed_title=feed_title,
        feed_url=feed_url,
    )


class TestCache:
    def test_save_and_load(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "articles.db"
        articles = [_make_article()]
        with patch("rss_cli.services.cache.cache_file_path", return_value=cache_path):
            with patch("rss_cli.services.cache.get_config") as mock_cfg:
                mock_cfg.return_value.cache_ttl_seconds = 999999
                save_cache(articles)
                loaded = load_cache()
                assert loaded is not None
                assert len(loaded) == 1
                assert loaded[0].title == "Test"

    def test_load_missing_returns_none(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "nonexistent.db"
        with patch("rss_cli.services.cache.cache_file_path", return_value=cache_path):
            assert load_cache() is None


class TestGroupByFeed:
    def test_groups_articles(self) -> None:
        articles = [
            _make_article("A1", feed_title="Feed 1", feed_url="http://f1.com"),
            _make_article("A2", feed_title="Feed 1", feed_url="http://f1.com"),
            _make_article("B1", feed_title="Feed 2", feed_url="http://f2.com"),
        ]

        feeds = group_by_feed(articles)
        assert len(feeds) == 2


class TestReadState:
    def test_mark_and_load(self, tmp_path: Path) -> None:
        invalidate_state_cache()
        state_path = tmp_path / "read_state.json"
        with patch("rss_cli.services.cache.read_state_path", return_value=state_path):
            mark_article_read("https://example.com/a1")
            state = load_read_state()
            assert "https://example.com/a1" in state

    def test_apply_read_state(self, tmp_path: Path) -> None:
        invalidate_state_cache()
        state_path = tmp_path / "read_state.json"
        state_path.write_text(json.dumps({"read": ["https://example.com/a1"]}))
        articles = [
            _make_article(link="https://example.com/a1"),
            _make_article(link="https://example.com/a2"),
        ]
        with patch("rss_cli.services.cache.read_state_path", return_value=state_path):
            result = apply_read_state(articles)
            assert result[0].is_read is True
            assert result[1].is_read is False


class TestBookmarks:
    def test_toggle_bookmark_add(self, tmp_path: Path) -> None:
        invalidate_state_cache()
        bm_path = tmp_path / "bookmarks.json"
        with patch("rss_cli.services.cache.bookmarks_path", return_value=bm_path):
            result = toggle_bookmark("https://example.com/a1")
            assert result is True

    def test_toggle_bookmark_remove(self, tmp_path: Path) -> None:
        invalidate_state_cache()
        bm_path = tmp_path / "bookmarks.json"
        with patch("rss_cli.services.cache.bookmarks_path", return_value=bm_path):
            toggle_bookmark("https://example.com/a1")
            result = toggle_bookmark("https://example.com/a1")
            assert result is False

    def test_apply_bookmark_state(self, tmp_path: Path) -> None:
        invalidate_state_cache()
        bm_path = tmp_path / "bookmarks.json"
        bm_path.write_text(json.dumps({"bookmarks": ["https://example.com/a1"]}))
        articles = [
            _make_article(link="https://example.com/a1"),
            _make_article(link="https://example.com/a2"),
        ]
        with patch("rss_cli.services.cache.bookmarks_path", return_value=bm_path):
            result = apply_bookmark_state(articles)
            assert result[0].is_bookmarked is True
            assert result[1].is_bookmarked is False

    def test_apply_all_state(self, tmp_path: Path) -> None:
        invalidate_state_cache()
        read_path = tmp_path / "read_state.json"
        bm_path = tmp_path / "bookmarks.json"
        read_path.write_text(json.dumps({"read": ["https://example.com/a1"]}))
        bm_path.write_text(json.dumps({"bookmarks": ["https://example.com/a2"]}))
        articles = [
            _make_article(link="https://example.com/a1"),
            _make_article(link="https://example.com/a2"),
        ]
        with (
            patch("rss_cli.services.cache.read_state_path", return_value=read_path),
            patch("rss_cli.services.cache.bookmarks_path", return_value=bm_path),
        ):
            result = apply_all_state(articles)
            assert result[0].is_read is True
            assert result[0].is_bookmarked is False
            assert result[1].is_read is False
            assert result[1].is_bookmarked is True
