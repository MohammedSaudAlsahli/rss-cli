"""Article Reader screen — display full article content."""

from __future__ import annotations

import webbrowser

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, Static

from rss_cli.models.article import Article
from rss_cli.services.cache import toggle_bookmark
from rss_cli.services.content_fetcher import fetch_article_content


class ReaderScreen(Screen[None]):
    """Screen for reading article content."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("o", "open_browser", "Open", show=True),
        Binding("b", "toggle_bookmark", "Bookmark", show=True),
        Binding("n", "next_article", "Next", show=True),
        Binding("p", "prev_article", "Prev", show=True),
        Binding("f", "fetch_full", "Full article", show=True),
    ]

    CSS = """
    ReaderScreen {
        layout: vertical;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.article: Article | None = None
        self._fetched_content: str = ""
        self._fetching: bool = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="reader-header")
        with VerticalScroll(id="reader-content"):
            yield Markdown("", id="article-markdown")
        yield Footer()

    def set_article(self, article: Article) -> None:
        self.article = article
        self._fetched_content = ""
        self._fetching = False
        self._display_article()

    def _display_article(self) -> None:
        if self.article is None:
            return

        a = self.article

        header = self.query_one("#reader-header", Static)
        meta_parts = [a.pub_date_display, a.feed_name, a.feed_title]
        bookmark_prefix = "• " if a.is_bookmarked else ""
        header.update(
            f" [bold cyan]{bookmark_prefix}[/][bold]{a.title}[/]\n"
            f" [dim]{' · '.join(meta_parts)}[/]"
        )

        content_parts: list[str] = []

        # Show loading state while fetching
        if self._fetching:
            content_parts.append("⏳ Fetching full article from the web…")

        # Try fetched content first (from "Fetch full" action)
        elif self._fetched_content:
            content_parts.append(self._fetched_content)

        elif a.parsed_content:
            # Use cached parsed content from RSS feed
            content_parts.append(a.parsed_content)

        if not content_parts:
            content_parts.append("*No content available in feed.*")
            if a.link:
                content_parts.append(
                    "Press **[f]** to fetch the full article from the web."
                )

        if a.link and not self._fetching:
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

    def action_fetch_full(self) -> None:
        """Fetch the full article content from the web."""
        if self.article is None:
            return
        if not self.article.link:
            self.notify("No link to fetch", severity="warning")
            return
        if self._fetching:
            return  # Already fetching

        self._fetching = True
        self._display_article()  # Show loading state
        self.notify("Fetching full article…", severity="information")
        self.run_worker(self._fetch_and_display())

    async def _fetch_and_display(self) -> None:
        if self.article is None:
            self._fetching = False
            return

        content = await fetch_article_content(self.article.link)
        self._fetching = False

        if content:
            self._fetched_content = content
            self._display_article()
            self.notify("✓ Full article loaded", severity="information")
        else:
            # Show helpful error message in the content area
            self._display_article()
            self.notify(
                "Could not fetch article — the site may block automated requests. "
                "Try pressing [o] to open in browser.",
                severity="warning",
            )

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
