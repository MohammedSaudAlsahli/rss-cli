"""Tests for RSS CLI models."""

from datetime import datetime

from rss_cli.models.feed import Article, _format_date, _parse_date


class TestParseDate:
    def test_rfc_2822_format(self) -> None:
        result = _parse_date("Mon, 23 Apr 2026 10:00:00 +0000")
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 4

    def test_iso_8601_format(self) -> None:
        result = _parse_date("2026-04-23T10:00:00+00:00")
        assert isinstance(result, datetime)

    def test_none_returns_min(self) -> None:
        result = _parse_date(None)
        assert result == datetime.min

    def test_empty_returns_min(self) -> None:
        result = _parse_date("")
        assert result == datetime.min

    def test_invalid_returns_min(self) -> None:
        result = _parse_date("not a date at all")
        assert result == datetime.min


class TestFormatDate:
    def test_valid_date(self) -> None:
        result = _format_date("Mon, 23 Apr 2026 10:00:00 +0000")
        assert result == "23/04 10:00"

    def test_none_returns_unknown(self) -> None:
        result = _format_date(None)
        assert result == "Unknown"


class TestArticle:
    def test_from_feedparser_entry(self) -> None:
        class MockEntry:
            title = "Test Article"
            link = "https://example.com/article"
            description = "A test article"
            summary = "Summary text"
            content = [{"value": "<p>Full content</p>"}]
            author = "John Doe"
            published = "Mon, 23 Apr 2026 10:00:00 +0000"
            updated = ""
            links = [{"href": "https://example.com/article"}]
            tags = []

        article = Article.from_feedparser_entry(
            MockEntry(), "Test Feed", "https://example.com/feed"
        )
        assert article.title == "Test Article"
        assert article.link == "https://example.com/article"
        assert article.author == "John Doe"
        assert article.feed_title == "Test Feed"
        assert article.is_read is False
        assert article.is_bookmarked is False

    def test_from_feedparser_entry_missing_fields(self) -> None:
        class MockEntry:
            pass

        article = Article.from_feedparser_entry(
            MockEntry(), "Test Feed", "https://example.com/feed"
        )
        assert article.title == "Untitled"
        assert article.link == ""
        assert article.author == ""

    def test_pub_date_display(self) -> None:
        article = Article(
            title="Test",
            link="https://example.com",
            description="",
            content="",
            author="",
            pub_date="Mon, 23 Apr 2026 10:00:00 +0000",
            tags=[],
            feed_title="Feed",
            feed_url="https://example.com/feed",
        )
        assert article.pub_date_display == "23/04 10:00"

    def test_short_description(self) -> None:
        article = Article("T", "l", "A" * 200, "", "", "", [], "F", "u")
        assert len(article.short_description) <= 120
        assert article.short_description.endswith("...")

    def test_feed_name_extracts_domain(self) -> None:
        article = Article(
            "T",
            "l",
            "",
            "",
            "",
            "",
            [],
            "F",
            "https://news.ycombinator.com/rss",
        )
        assert article.feed_name == "ycombinator"

    def test_feed_name_strips_www(self) -> None:
        article = Article(
            "T",
            "l",
            "",
            "",
            "",
            "",
            [],
            "F",
            "https://www.example.com/feed.xml",
        )
        assert article.feed_name == "example"

    def test_feed_name_strips_news_prefix(self) -> None:
        article = Article(
            "T",
            "l",
            "",
            "",
            "",
            "",
            [],
            "F",
            "https://news.google.com/rss",
        )
        assert article.feed_name == "google"
