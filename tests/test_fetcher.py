"""Tests for the fetcher service — Nitter fallback logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from rss_cli.services.fetcher import _fetch_feed, _nitter_path


def _make_response(text: str = "", *, raise_on_status: bool = False) -> MagicMock:
    """Create a mock httpx.Response with a plain string .text attribute."""
    resp = MagicMock(spec=httpx.Response)
    resp.text = text
    if raise_on_status:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock()
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


class TestNitterPath:
    def test_extracts_path_from_known_instance(self) -> None:
        with patch(
            "rss_cli.services.fetcher.get_nitter_instances",
            return_value=["nitter.net", "xcancel.com"],
        ):
            assert _nitter_path("https://nitter.net/elonmusk/rss") == "/elonmusk/rss"

    def test_returns_none_for_non_nitter(self) -> None:
        with patch(
            "rss_cli.services.fetcher.get_nitter_instances",
            return_value=["nitter.net"],
        ):
            assert _nitter_path("https://example.com/feed.xml") is None

    def test_returns_none_for_nitter_non_rss_path(self) -> None:
        with patch(
            "rss_cli.services.fetcher.get_nitter_instances",
            return_value=["nitter.net"],
        ):
            assert _nitter_path("https://nitter.net/elonmusk") is None


class TestFetchFeedFallback:
    @pytest.mark.asyncio
    async def test_primary_succeeds_no_fallback(self) -> None:
        """If the primary URL works, fallback should not be attempted."""
        client = AsyncMock()
        client.get.return_value = _make_response(
            '<rss><channel><title>Test</title></channel></rss>'
        )

        with patch(
            "rss_cli.services.fetcher.get_nitter_instances",
            return_value=["nitter.net", "xcancel.com"],
        ):
            with patch("rss_cli.services.fetcher.get_config") as mock_cfg:
                mock_cfg.return_value.max_articles_per_feed = 50
                result = await _fetch_feed(client, "https://nitter.net/user/rss")

        assert isinstance(result, list)
        assert client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_primary_fails_tries_fallback(self) -> None:
        """If primary Nitter instance fails, should try the next instance."""
        client = AsyncMock()
        fail_resp = _make_response(raise_on_status=True)
        success_resp = _make_response(
            '<rss><channel><title>Fallback</title></channel></rss>'
        )
        client.get = AsyncMock(side_effect=[fail_resp, success_resp])

        with patch(
            "rss_cli.services.fetcher.get_nitter_instances",
            return_value=["nitter.net", "xcancel.com"],
        ):
            with patch("rss_cli.services.fetcher.get_config") as mock_cfg:
                mock_cfg.return_value.max_articles_per_feed = 50
                result = await _fetch_feed(client, "https://nitter.net/user/rss")

        assert isinstance(result, list)
        assert client.get.call_count == 2  # Primary + 1 fallback

    @pytest.mark.asyncio
    async def test_non_nitter_failure_no_fallback(self) -> None:
        """Non-Nitter URLs that fail should NOT trigger fallback."""
        client = AsyncMock()
        client.get.return_value = _make_response(raise_on_status=True)

        with patch(
            "rss_cli.services.fetcher.get_nitter_instances",
            return_value=["nitter.net", "xcancel.com"],
        ):
            with patch("rss_cli.services.fetcher.get_config") as mock_cfg:
                mock_cfg.return_value.max_articles_per_feed = 50
                result = await _fetch_feed(client, "https://example.com/feed.xml")

        assert result == []
        assert client.get.call_count == 1
