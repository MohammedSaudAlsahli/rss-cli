"""HTML to Markdown conversion for article content display."""

from __future__ import annotations

import re


def html_to_markdown(html: str) -> str:
    """Convert HTML to Markdown suitable for Textual's Markdown widget.

    Handles common HTML elements: headings, paragraphs, lists, links,
    images, bold, italic, code, blockquotes, tables, and more.
    """
    if not html or not html.strip():
        return ""

    text = html

    # --- Pre-processing: normalize whitespace ---
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\r", "\n", text)

    # --- Remove script and style blocks entirely ---
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<noscript[^>]*>.*?</noscript>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # --- Headings ---
    for level in range(1, 7):
        text = re.sub(
            rf"<h{level}[^>]*>(.*?)</h{level}>",
            rf"\n{'#' * level} \1\n",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

    # --- Block-level elements ---
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?div[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?section[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?article[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?main[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?header[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?footer[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?aside[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?figure[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?figcaption[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?details[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?summary[^>]*>", "\n", text, flags=re.IGNORECASE)

    # --- Lists ---
    text = re.sub(r"</?ul[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?ol[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)

    # --- Definition lists ---
    text = re.sub(r"</?dl[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<dt[^>]*>", "\n**", text, flags=re.IGNORECASE)
    text = re.sub(r"</dt>", "** ", text, flags=re.IGNORECASE)
    text = re.sub(r"<dd[^>]*>", "  ", text, flags=re.IGNORECASE)
    text = re.sub(r"</dd>", "\n", text, flags=re.IGNORECASE)

    # --- Inline formatting ---
    text = re.sub(r"<strong[^>]*>", "**", text, flags=re.IGNORECASE)
    text = re.sub(r"</strong>", "**", text, flags=re.IGNORECASE)
    text = re.sub(r"<b[^>]*>", "**", text, flags=re.IGNORECASE)
    text = re.sub(r"</b>", "**", text, flags=re.IGNORECASE)
    text = re.sub(r"<em[^>]*>", "*", text, flags=re.IGNORECASE)
    text = re.sub(r"</em>", "*", text, flags=re.IGNORECASE)
    text = re.sub(r"<i[^>]*>", "*", text, flags=re.IGNORECASE)
    text = re.sub(r"</i>", "*", text, flags=re.IGNORECASE)
    text = re.sub(r"<u[^>]*>", "__", text, flags=re.IGNORECASE)
    text = re.sub(r"</u>", "__", text, flags=re.IGNORECASE)
    text = re.sub(r"<s[^>]*>", "~~", text, flags=re.IGNORECASE)
    text = re.sub(r"</s>", "~~", text, flags=re.IGNORECASE)
    text = re.sub(r"<del[^>]*>", "~~", text, flags=re.IGNORECASE)
    text = re.sub(r"</del>", "~~", text, flags=re.IGNORECASE)

    # --- Code ---
    text = re.sub(r"<code[^>]*>", "`", text, flags=re.IGNORECASE)
    text = re.sub(r"</code>", "`", text, flags=re.IGNORECASE)
    text = re.sub(r"<pre[^>]*>", "\n```\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</pre>", "\n```\n", text, flags=re.IGNORECASE)

    # --- Links: extract href and text ---
    def _replace_link(match: re.Match[str]) -> str:
        href = match.group(1) or ""
        # The link text will be whatever is between > and </a>
        # We'll handle it after this pass
        return f"[{href}]("

    # Convert <a href="url">text</a> to [text](url)
    def _replace_link_full(match: re.Match[str]) -> str:
        href = match.group(1) or ""
        link_text = match.group(2) or ""
        # Clean up link text
        link_text = re.sub(r"<[^>]+>", "", link_text).strip()
        if not link_text:
            link_text = href
        if len(link_text) > 80:
            link_text = link_text[:77] + "..."
        return f"[{link_text}]({href})"

    text = re.sub(
        r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        _replace_link_full,
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # --- Images: extract alt text and src ---
    def _replace_img(match: re.Match[str]) -> str:
        alt = match.group(1) or "image"
        src = match.group(2) or ""
        if src:
            return f"![{alt}]({src})"
        return f"*[{alt}]*"

    text = re.sub(
        r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*/?>',
        _replace_img,
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>',
        lambda m: f"![{m.group(2)}]({m.group(1)})",
        text,
        flags=re.IGNORECASE,
    )
    # Images without alt
    text = re.sub(
        r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>',
        lambda m: f"![image]({m.group(1)})",
        text,
        flags=re.IGNORECASE,
    )

    # --- Blockquotes ---
    text = re.sub(r"<blockquote[^>]*>", "\n> ", text, flags=re.IGNORECASE)
    text = re.sub(r"</blockquote>", "\n", text, flags=re.IGNORECASE)

    # --- Horizontal rules ---
    text = re.sub(r"<hr\s*/?>", "\n---\n", text, flags=re.IGNORECASE)

    # --- Tables (basic conversion) ---
    text = re.sub(r"</?table[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?thead[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?tbody[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?tr[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?th[^>]*>", " **", text, flags=re.IGNORECASE)
    text = re.sub(r"</th>", "** ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?td[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</td>", " |", text, flags=re.IGNORECASE)

    # --- Remove all remaining HTML tags ---
    text = re.sub(r"<[^>]+>", "", text)

    # --- Decode common HTML entities ---
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#8217;", "'")
    text = text.replace("&#8216;", "'")
    text = text.replace("&#8220;", '"')
    text = text.replace("&#8221;", '"')
    text = text.replace("&#8212;", "—")
    text = text.replace("&#8211;", "–")
    text = text.replace("&#8230;", "…")

    # --- Clean up whitespace ---
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def html_to_text(html: str) -> str:
    """Strip basic HTML tags for display. Delegates to html_to_markdown for richer output."""
    return html_to_markdown(html)
