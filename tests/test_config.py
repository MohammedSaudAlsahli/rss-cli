"""Tests for config service."""

from pathlib import Path
from unittest.mock import patch

from rss_cli.services.config import (
    load_feed_urls,
    remove_feed_url,
    save_feed_url,
)


class TestFeedUrls:
    def test_save_and_load(self, tmp_path: Path) -> None:
        feeds_path = tmp_path / "feeds.txt"
        with patch("rss_cli.services.config.feeds_file_path", return_value=feeds_path):
            save_feed_url("https://example.com/feed.xml")
            urls = load_feed_urls()
            assert "https://example.com/feed.xml" in urls

    def test_save_duplicate_returns_false(self, tmp_path: Path) -> None:
        feeds_path = tmp_path / "feeds.txt"
        with patch("rss_cli.services.config.feeds_file_path", return_value=feeds_path):
            save_feed_url("https://example.com/feed.xml")
            result = save_feed_url("https://example.com/feed.xml")
            assert result is False

    def test_remove_existing(self, tmp_path: Path) -> None:
        feeds_path = tmp_path / "feeds.txt"
        with patch("rss_cli.services.config.feeds_file_path", return_value=feeds_path):
            save_feed_url("https://example.com/feed.xml")
            result = remove_feed_url("https://example.com/feed.xml")
            assert result is True
            assert load_feed_urls() == []

    def test_remove_nonexistent(self, tmp_path: Path) -> None:
        feeds_path = tmp_path / "feeds.txt"
        with patch("rss_cli.services.config.feeds_file_path", return_value=feeds_path):
            result = remove_feed_url("https://example.com/feed.xml")
            assert result is False

    def test_load_empty(self, tmp_path: Path) -> None:
        feeds_path = tmp_path / "feeds.txt"
        with patch("rss_cli.services.config.feeds_file_path", return_value=feeds_path):
            assert load_feed_urls() == []

    def test_ignores_comments_and_blank_lines(self, tmp_path: Path) -> None:
        feeds_path = tmp_path / "feeds.txt"
        feeds_path.write_text("# comment\n\nhttps://example.com/feed.xml\n\n")
        with patch("rss_cli.services.config.feeds_file_path", return_value=feeds_path):
            urls = load_feed_urls()
            assert urls == ["https://example.com/feed.xml"]
