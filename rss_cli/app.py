"""Main Textual application for RSS CLI."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.theme import Theme
from textual.widgets import Footer, Header

from rss_cli.models.feed import Article, Feed
from rss_cli.services.feed_service import fetch_feeds

# Tokyo Night-inspired dark theme
TOKYO_NIGHT = Theme(
    name="tokyo-night",
    primary="#7aa2f7",
    secondary="#bb9af7",
    accent="#7dcfff",
    warning="#e0af68",
    error="#f7768e",
    success="#9ece6a",
    foreground="#c0caf5",
    background="#1a1b26",
    surface="#1f2335",
    panel="#292e42",
    dark=True,
    variables={
        "input-selection-background": "#7aa2f7 30%",
        "footer-key-foreground": "#7aa2f7",
        "block-cursor-foreground": "#1a1b26",
        "block-cursor-background": "#7aa2f7",
    },
)

# Nord-inspired dark theme
NORD = Theme(
    name="nord",
    primary="#88c0d0",
    secondary="#81a1c1",
    accent="#b48ead",
    warning="#ebcb8b",
    error="#bf616a",
    success="#a3be8c",
    foreground="#d8dee9",
    background="#2e3440",
    surface="#3b4252",
    panel="#434c5e",
    dark=True,
    variables={
        "input-selection-background": "#88c0d0 30%",
        "footer-key-foreground": "#88c0d0",
        "block-cursor-foreground": "#2e3440",
        "block-cursor-background": "#88c0d0",
    },
)

# Catppuccin Mocha dark theme
CATPPUCCIN = Theme(
    name="catppuccin",
    primary="#cba6f7",
    secondary="#f5c2e7",
    accent="#89dceb",
    warning="#f9e2af",
    error="#f38ba8",
    success="#a6e3a1",
    foreground="#cdd6f4",
    background="#1e1e2e",
    surface="#181825",
    panel="#313244",
    dark=True,
    variables={
        "input-selection-background": "#cba6f7 30%",
        "footer-key-foreground": "#cba6f7",
        "block-cursor-foreground": "#1e1e2e",
        "block-cursor-background": "#cba6f7",
    },
)


class RssCliApp(App[None]):
    """A beautiful terminal RSS feed reader."""

    TITLE = "RSS CLI"

    CSS = """
    #main-container {
        height: 1fr;
    }
    #article-panel {
        width: 1fr;
    }
    #article-list {
        height: 1fr;
    }
    #right-panel {
        width: 2fr;
        border-left: solid $primary;
    }
    #preview-title {
        padding: 0 1;
        color: $text;
        height: auto;
        text-style: bold;
    }
    #preview-meta {
        padding: 0 1;
        color: $text-disabled;
        height: auto;
        border-bottom: solid $primary;
    }
    #preview-scroll {
        height: 1fr;
    }
    #preview-content {
        padding: 0 1;
    }
    #bookmarks-list {
        height: 1fr;
    }
    TabbedContent {
        height: 1fr;
    }
    #reader-header {
        height: auto;
        padding: 1 2;
        background: $surface;
        border-bottom: solid $primary;
    }
    #reader-content {
        height: 1fr;
        padding: 1 2;
    }
    #input-dialog {
        width: 60;
        height: 10;
        padding: 1 2;
        background: $surface;
        border: round $primary;
    }
    #prompt-label {
        margin-bottom: 1;
    }
    #url-input {
        margin-bottom: 1;
    }
    Footer {
        dock: bottom;
    }
    """

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
        self._themes = [TOKYO_NIGHT, NORD, CATPPUCCIN]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Footer()

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

    async def action_refresh(self) -> None:
        """Refresh all feeds."""
        self.feeds = await fetch_feeds()
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


# Import screens at bottom to avoid circular imports
from rss_cli.screens.dashboard import DashboardScreen  # noqa: E402
from rss_cli.screens.reader import ReaderScreen  # noqa: E402
