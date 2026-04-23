"""Main Textual application for RSS CLI."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from rss_cli.models.article import Article, Feed
from rss_cli.screens.dashboard import DashboardScreen
from rss_cli.screens.reader import ReaderScreen
from rss_cli.services.fetcher import fetch_feeds
from rss_cli.themes import THEMES


class RssCliApp(App[None]):
    """A beautiful terminal RSS feed reader."""

    TITLE = "RSS CLI"

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("question_mark", "show_help_panel", "Help", key_display="?"),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("t", "cycle_theme", "Theme", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.feeds: list[Feed] = []
        self.all_articles: list[Article] = []
        self._theme_index = 0
        self._themes = THEMES

    def on_mount(self) -> None:
        """Register themes, apply default, and load dashboard."""
        for theme in self._themes:
            self.register_theme(theme)
        self.theme = "tokyo-night"

        self.install_screen(
            lambda: DashboardScreen(),  # type: ignore[arg-type]
            name="dashboard",
        )
        self.install_screen(
            lambda: ReaderScreen(),  # type: ignore[arg-type]
            name="reader",
        )
        self.push_screen("dashboard")
        self.run_worker(self.action_refresh())

    def action_cycle_theme(self) -> None:
        """Cycle through available dark themes."""
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        theme = self._themes[self._theme_index]
        self.theme = theme.name
        self.notify(f"Theme: {theme.name}", severity="information")

    async def action_refresh(self, force: bool = False) -> None:
        """Refresh all feeds. Uses cache unless force=True."""
        self.feeds = await fetch_feeds(force=force)
        self.all_articles = []
        for feed in self.feeds:
            self.all_articles.extend(feed.articles)

        try:
            screen = self.get_screen("dashboard")
            if hasattr(screen, "update_feeds"):
                screen.update_feeds(self.feeds)
        except Exception:
            pass

    def go_to_reader(self, article: Article) -> None:
        """Navigate to article reader."""
        try:
            screen = self.get_screen("reader")
            if hasattr(screen, "set_article"):
                screen.set_article(article)
            self.push_screen("reader")
        except Exception:
            pass

    def go_next_article(self) -> None:
        """Navigate to next article from reader."""
        self._navigate_article(1)

    def go_prev_article(self) -> None:
        """Navigate to previous article from reader."""
        self._navigate_article(-1)

    def _navigate_article(self, offset: int) -> None:
        try:
            reader = self.get_screen("reader")
            article = getattr(reader, "article", None)
            if article is None:
                return
            try:
                idx = self.all_articles.index(article)
            except ValueError:
                return
            new_idx = idx + offset
            if 0 <= new_idx < len(self.all_articles):
                new_article = self.all_articles[new_idx]
                from rss_cli.services.cache import mark_article_read

                mark_article_read(new_article.link)
                new_article.is_read = True
                if hasattr(reader, "set_article"):
                    reader.set_article(new_article)

            try:
                dashboard = self.get_screen("dashboard")
                if hasattr(dashboard, "refresh_state"):
                    dashboard.refresh_state()
            except Exception:
                pass
        except Exception:
            pass
