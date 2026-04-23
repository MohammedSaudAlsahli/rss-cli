"""Article Reader screen — display full article content."""

from __future__ import annotations

import webbrowser

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, Static

from rss_cli.models.feed import Article
from rss_cli.services.cache import toggle_bookmark

_SKIP_CONTENT = {"[comments]", "comments", ""}


class ReaderScreen(Screen[None]):
    """Screen for reading article content."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("o", "open_browser", "Browser", show=True),
        Binding("b", "toggle_bookmark", "Bookmark", show=True),
        Binding("n", "next_article", "Next", show=True),
        Binding("p", "prev_article", "Prev", show=True),
    ]

    CSS = """
    ReaderScreen {
        layout: vertical;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.article: Article | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="reader-header")
        with VerticalScroll(id="reader-content"):
            yield Markdown("", id="article-markdown")
        yield Footer()

    def set_article(self, article: Article) -> None:
        self.article = article
        self._display_article()

    def _display_article(self) -> None:
        if self.article is None:
            return

        a = self.article

        header = self.query_one("#reader-header", Static)
        meta_parts = [a.pub_date_display, a.feed_name, a.feed_title]
        bookmark_style = " bold cyan" if a.is_bookmarked else ""
        header.update(
            f" [bold{bookmark_style}]{a.title}[/]\n"
            f" [dim]{'  ·  '.join(meta_parts)}[/]"
        )

        content_parts: list[str] = []

        if a.content:
            cleaned = _html_to_text(a.content)
            if cleaned.strip().lower() not in _SKIP_CONTENT:
                content_parts.append(cleaned)
            elif a.description:
                cleaned_desc = _html_to_text(a.description)
                if cleaned_desc.strip().lower() not in _SKIP_CONTENT:
                    content_parts.append(cleaned_desc)
        elif a.description:
            cleaned = _html_to_text(a.description)
            if cleaned.strip().lower() not in _SKIP_CONTENT:
                content_parts.append(cleaned)

        if not content_parts:
            content_parts.append("*No content available.*")

        if a.link:
            content_parts.append(f"\n---\n[Open in browser]({a.link})")

        if a.tags:
            content_parts.append(f"\n**Tags:** {', '.join(a.tags)}")

        markdown = self.query_one("#article-markdown", Markdown)
        markdown.update("\n\n".join(content_parts))

    def action_toggle_bookmark(self) -> None:
        if self.article is None:
            return
        is_new = toggle_bookmark(self.article.link)
        self.article.is_bookmarked = is_new
        label = "Bookmarked" if is_new else "Bookmark removed"
        self.notify(label, severity="information")
        self._display_article()

    def action_open_browser(self) -> None:
        if self.article and self.article.link:
            webbrowser.open(self.article.link)
        else:
            self.notify("No link available", severity="warning")

    def action_go_back(self) -> None:
        # Refresh dashboard read/bookmark state before going back
        try:
            dashboard = self.app.get_screen("dashboard")
            if hasattr(dashboard, "refresh_state"):
                dashboard.refresh_state()
        except Exception:
            pass
        self.app.pop_screen()

    def action_next_article(self) -> None:
        app = self.app
        if hasattr(app, "go_next_article"):
            app.go_next_article()

    def action_prev_article(self) -> None:
        app = self.app
        if hasattr(app, "go_prev_article"):
            app.go_prev_article()


def _html_to_text(html: str) -> str:
    """Strip basic HTML tags for display."""
    import re

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
