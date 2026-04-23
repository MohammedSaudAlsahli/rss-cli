"""Utility functions for RSS CLI."""

from __future__ import annotations

import re

SKIP_CONTENT: frozenset[str] = frozenset({"[comments]", "comments", ""})


def html_to_text(html: str) -> str:
    """Strip basic HTML tags for display."""
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</?p\s*>", "\n", text)
    text = re.sub(r"</?div\s*>", "\n", text)
    text = re.sub(r"<h[1-6][^>]*>", "\n## ", text)
    text = re.sub(r"</h[1-6]>", "\n", text)
    text = re.sub(r"<li[^>]*>", "- ", text)
    text = re.sub(r"<strong[^>]*>", "**", text)
    text = re.sub(r"</strong>", "**", text)
    text = re.sub(r"<em[^>]*>", "*", text)
    text = re.sub(r"</em>", "*", text)
    text = re.sub(r"<a[^>]*href=['\"]([^'\"]*)['\"][^>]*>", "[", text)
    text = re.sub(r"</a>", "]", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
