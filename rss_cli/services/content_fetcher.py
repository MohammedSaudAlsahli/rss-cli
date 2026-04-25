"""Fetch full article content from web pages when RSS content is insufficient."""

from __future__ import annotations

import logging

import httpx

from rss_cli.markup import html_to_markdown

logger = logging.getLogger(__name__)

# Cache for fetched content: URL → extracted text
_content_cache: dict[str, str] = {}

# Browser-like User-Agent to avoid being blocked by most sites
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


async def fetch_article_content(url: str) -> str:
    """Fetch a web page and extract its main readable content.

    Uses readability-lxml to extract the article body, then
    converts HTML to Markdown for display in the terminal.

    Returns empty string if fetching or parsing fails.
    """
    if url in _content_cache:
        return _content_cache[url]

    # Step 1: Fetch the page
    html = await _fetch_page(url)
    if not html:
        return ""

    # Step 2: Extract readable content
    content = _extract_content(html)
    if not content:
        return ""

    # Step 3: Cache and return
    _content_cache[url] = content
    return content


async def _fetch_page(url: str) -> str:
    """Fetch a web page, returning its HTML or empty string on failure."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=10.0),
            follow_redirects=True,
            max_redirects=5,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            # Only process HTML responses
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                logger.debug("Skipping non-HTML content type: %s for %s", content_type, url)
                return ""
            return response.text
    except httpx.TimeoutException:
        logger.debug("Timeout fetching %s", url)
        return ""
    except httpx.HTTPStatusError as exc:
        logger.debug("HTTP %d fetching %s", exc.response.status_code, url)
        return ""
    except httpx.HTTPError:
        logger.debug("Network error fetching %s", url)
        return ""


def _extract_content(html: str) -> str:
    """Extract readable content from HTML using readability-lxml.

    Falls back to simple HTML-to-Markdown conversion if readability fails.
    """
    try:
        from readability import Document  # type: ignore[import-untyped]

        doc = Document(html)
        summary_html = doc.summary()
    except Exception:
        logger.debug("readability-lxml failed, using simple extraction")
        return _simple_extract(html)

    if not summary_html or not summary_html.strip():
        return _simple_extract(html)

    text = html_to_markdown(summary_html)
    if not text.strip():
        return _simple_extract(html)

    return text


def _simple_extract(html: str) -> str:
    """Fallback: convert HTML to Markdown without readability extraction."""
    text = html_to_markdown(html)
    if not text.strip():
        return ""
    # Truncate very long pages to avoid overwhelming the terminal
    if len(text) > 15000:
        text = text[:15000] + "\n\n... (content truncated)"
    return text


def clear_content_cache() -> None:
    """Clear the cached fetched content."""
    _content_cache.clear()
