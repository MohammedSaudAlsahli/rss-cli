"""Dashboard — articles/bookmarks left (1fr), preview right (2fr)."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, OptionList, Static, TabbedContent, TabPane
from textual.widgets.option_list import Option

from rss_cli.models.feed import Article, Feed
from rss_cli.services.cache import apply_all_state, mark_article_read, toggle_bookmark
from rss_cli.services.config import load_feed_urls, remove_feed_url, save_feed_url

_SKIP_CONTENT = {"[comments]", "comments", ""}


class DashboardScreen(Screen[None]):
    """Main dashboard: article list left, preview/bookmarks right."""

    BINDINGS = [
        Binding("b", "toggle_bookmark", "Bookmark", show=True),
        Binding("o", "open_browser", "Browser", show=True),
        Binding("enter", "read_article", "Read", show=True),
        Binding("s", "search", "Search", show=True),
        Binding("a", "add_feed", "Add feed", show=True),
        Binding("d", "delete_feed", "Del feed", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS = """
    DashboardScreen {
        layout: vertical;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.feeds: list[Feed] = []
        self.all_articles: list[Article] = []
        self._filtered_articles: list[Article] = []
        self._selected_article: Article | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            with Vertical(id="article-panel"):
                with TabbedContent(id="left-tabs"):
                    with TabPane("Articles", id="articles-tab"):
                        yield OptionList(id="article-list")
                    with TabPane("Bookmarks", id="bookmarks-tab"):
                        yield OptionList(id="bookmarks-list")
            with Vertical(id="right-panel"):
                yield Static("", id="preview-title")
                yield Static("", id="preview-meta")
                with VerticalScroll(id="preview-scroll"):
                    yield Markdown("", id="preview-content")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_articles()
        self._populate_bookmarks()
        # Focus the article list and highlight the first item
        list_widget = self.query_one("#article-list", OptionList)
        list_widget.focus()
        if list_widget.option_count > 0:
            list_widget.highlighted = 0

    def refresh_state(self) -> None:
        """Re-apply read/bookmark state from disk and repopulate lists."""
        apply_all_state(self.all_articles)
        # Also re-apply to filtered list (same objects, so already updated)
        self._populate_articles()
        self._populate_bookmarks()

    def update_feeds(self, feeds: list[Feed]) -> None:
        self.feeds = feeds
        self.all_articles = []
        for feed in feeds:
            self.all_articles.extend(feed.articles)
        apply_all_state(self.all_articles)
        self._filtered_articles = list(self.all_articles)
        self._populate_articles()
        self._populate_bookmarks()

    def _make_meta_line(self, article: Article) -> str:
        """Build the second line: date · rss_name · feed_title."""
        parts = [article.pub_date_display, article.feed_name, article.feed_title]
        return " · ".join(parts)

    def _make_article_prompt(self, article: Article) -> Text:
        """Build a two-line Rich Text prompt: title + meta."""
        title_text = article.title
        if len(title_text) > 70:
            title_text = title_text[:67] + "..."
        title_style = "dim" if article.is_read else "bold white"
        cell = Text()
        if article.is_bookmarked:
            cell.append("• ", style="bold cyan")
        cell.append(title_text, style=title_style)
        cell.append("\n")
        cell.append(self._make_meta_line(article), style="dim")
        return cell

    def _make_bookmark_prompt(self, article: Article) -> Text:
        """Build a two-line Rich Text prompt for bookmarks: title + meta."""
        title_text = article.title
        if len(title_text) > 50:
            title_text = title_text[:47] + "..."
        title_style = "dim" if article.is_read else "bold white"
        cell = Text()
        cell.append("• ", style="bold cyan")
        cell.append(title_text, style=title_style)
        cell.append("\n")
        cell.append(self._make_meta_line(article), style="dim")
        return cell

    def _populate_articles(self) -> None:
        list_widget = self.query_one("#article-list", OptionList)
        list_widget.clear_options()

        if not self._filtered_articles:
            list_widget.add_option(
                Option(
                    Text(
                        "No articles yet. Press [r] to refresh or [a] to add a feed.",
                        style="dim",
                    ),
                    id="empty",
                )
            )
            return

        for i, article in enumerate(self._filtered_articles):
            list_widget.add_option(
                Option(
                    self._make_article_prompt(article),
                    id=f"article-{i}",
                )
            )

    def _populate_bookmarks(self) -> None:
        bookmarked = [a for a in self.all_articles if a.is_bookmarked]
        list_widget = self.query_one("#bookmarks-list", OptionList)
        list_widget.clear_options()

        if not bookmarked:
            list_widget.add_option(
                Option(
                    Text("No bookmarks yet. Press [b] to bookmark.", style="dim"),
                    id="empty-bm",
                )
            )
            return

        for i, article in enumerate(bookmarked):
            list_widget.add_option(
                Option(
                    self._make_bookmark_prompt(article),
                    id=f"bookmark-{i}",
                )
            )

    def _update_preview(self, article: Article) -> None:
        self._selected_article = article

        title_widget = self.query_one("#preview-title", Static)
        title_widget.update(f" [bold]{article.title}[/]")

        meta_widget = self.query_one("#preview-meta", Static)
        meta_parts = [article.pub_date_display, article.feed_title]
        if article.author:
            meta_parts.append(article.author)
        meta_widget.update(f" [dim]{'  ·  '.join(meta_parts)}[/]")

        content_parts: list[str] = []
        from rss_cli.screens.reader import _html_to_text

        if article.content and len(article.content) > len(article.description):
            cleaned = _html_to_text(article.content)
            if cleaned.strip().lower() not in _SKIP_CONTENT:
                content_parts.append(cleaned)
            elif article.description:
                cleaned2 = _html_to_text(article.description)
                if cleaned2.strip().lower() not in _SKIP_CONTENT:
                    content_parts.append(cleaned2)
        elif article.description:
            cleaned = _html_to_text(article.description)
            if cleaned.strip().lower() not in _SKIP_CONTENT:
                content_parts.append(cleaned)

        if not content_parts:
            if article.link:
                content_parts.append(f"**[Open in browser]({article.link})**")

        if article.tags:
            content_parts.append(f"**Tags:** {', '.join(article.tags)}")

        if not content_parts:
            content_parts.append("*No content available.*")

        preview = self.query_one("#preview-content", Markdown)
        preview.update("\n\n".join(content_parts))

        # Reset scroll position to top after content update
        scroll = self.query_one("#preview-scroll", VerticalScroll)
        scroll.scroll_home(animate=False)

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle selection in either the article list or bookmarks list."""
        option_id = event.option.id
        if option_id and option_id.startswith("article-"):
            idx = int(option_id.split("-", 1)[1])
            if 0 <= idx < len(self._filtered_articles):
                article = self._filtered_articles[idx]
                if not article.is_read:
                    mark_article_read(article.link)
                    article.is_read = True
                    self._populate_articles()
                    self._populate_bookmarks()
                    # Restore highlight after repopulation
                    list_widget = self.query_one("#article-list", OptionList)
                    if 0 <= idx < list_widget.option_count:
                        list_widget.highlighted = idx
                self._update_preview(article)
        elif option_id and option_id.startswith("bookmark-"):
            bookmarked = [a for a in self.all_articles if a.is_bookmarked]
            idx = int(option_id.split("-", 1)[1])
            if 0 <= idx < len(bookmarked):
                article = bookmarked[idx]
                if not article.is_read:
                    mark_article_read(article.link)
                    article.is_read = True
                    self._populate_articles()
                    self._populate_bookmarks()
                    bm_widget = self.query_one("#bookmarks-list", OptionList)
                    if 0 <= idx < bm_widget.option_count:
                        bm_widget.highlighted = idx
                self._update_preview(article)

    def action_read_article(self) -> None:
        list_widget = self.query_one("#article-list", OptionList)
        highlighted = list_widget.highlighted
        if highlighted is None or highlighted < 0 or highlighted >= len(
            self._filtered_articles
        ):
            self.notify("No article selected", severity="warning")
            return
        article = self._filtered_articles[highlighted]
        mark_article_read(article.link)
        article.is_read = True
        self._populate_articles()
        self._populate_bookmarks()
        # Restore highlight after repopulation
        if 0 <= highlighted < list_widget.option_count:
            list_widget.highlighted = highlighted

        app = self.app
        if hasattr(app, "go_to_reader"):
            app.go_to_reader(article)

    def action_toggle_bookmark(self) -> None:
        list_widget = self.query_one("#article-list", OptionList)
        highlighted = list_widget.highlighted
        if highlighted is None or highlighted < 0 or highlighted >= len(
            self._filtered_articles
        ):
            self.notify("No article selected", severity="warning")
            return
        article = self._filtered_articles[highlighted]
        is_bookmarked = toggle_bookmark(article.link)
        article.is_bookmarked = is_bookmarked
        label = "Bookmarked" if is_bookmarked else "Bookmark removed"
        self.notify(label, severity="information")
        self._populate_articles()
        self._populate_bookmarks()
        # Restore highlight to the same article after repopulation
        if 0 <= highlighted < list_widget.option_count:
            list_widget.highlighted = highlighted
        if self._selected_article and self._selected_article.link == article.link:
            self._update_preview(article)

    def action_open_browser(self) -> None:
        import webbrowser

        list_widget = self.query_one("#article-list", OptionList)
        highlighted = list_widget.highlighted
        if highlighted is None or highlighted < 0 or highlighted >= len(
            self._filtered_articles
        ):
            self.notify("No article selected", severity="warning")
            return
        article = self._filtered_articles[highlighted]
        if article.link:
            webbrowser.open(article.link)
        else:
            self.notify("No link available", severity="warning")

    def action_add_feed(self) -> None:
        def _on_result(result: str | None) -> None:
            if result:
                url = result.strip()
                if save_feed_url(url):
                    self.notify(f"Added: {url}", severity="information")
                    app = self.app
                    if hasattr(app, "action_refresh"):
                        app.run_worker(app.action_refresh(force=True))

        self.app.push_screen(_InputScreen("Enter RSS feed URL:", _on_result))

    def action_delete_feed(self) -> None:
        """Show a list of all feeds so the user can select one to delete."""
        feed_urls = load_feed_urls()
        if not feed_urls:
            self.notify("No feeds to delete", severity="warning")
            return
        # Build a map of feed titles from loaded feeds
        feed_titles: dict[str, str] = {}
        for feed in self.feeds:
            feed_titles[feed.url] = feed.title or feed.url
        # Fill in any URLs not in loaded feeds
        for url in feed_urls:
            if url not in feed_titles:
                feed_titles[url] = url
        self.app.push_screen(_FeedSelectScreen(feed_urls, feed_titles))

    def action_refresh(self) -> None:
        app = self.app
        if hasattr(app, "action_refresh"):
            app.run_worker(app.action_refresh(force=True))

    def action_view_all(self) -> None:
        self._filtered_articles = list(self.all_articles)
        self._populate_articles()

    def action_search(self) -> None:
        def _on_result(result: str | None) -> None:
            if result is None:
                return
            query = result.strip().lower()
            if not query:
                self._filtered_articles = list(self.all_articles)
            else:
                self._filtered_articles = [
                    a
                    for a in self.all_articles
                    if query in a.title.lower()
                    or query in a.description.lower()
                    or query in a.author.lower()
                    or query in a.feed_title.lower()
                ]
            self._populate_articles()

        self.app.push_screen(_InputScreen("Search articles:", _on_result))


class _InputScreen(Screen[None]):
    """Simple input dialog screen."""

    CSS = """
    _InputScreen {
        align: center middle;
    }
    """

    def __init__(self, prompt: str, callback: object) -> None:
        super().__init__()
        self.prompt_text = prompt
        self.callback = callback

    def compose(self) -> ComposeResult:
        from textual.widgets import Input, Label

        with Vertical(id="input-dialog"):
            yield Label(self.prompt_text, id="prompt-label")
            yield Input(placeholder="https://example.com/feed.xml", id="url-input")

    def on_input_submitted(self, event: object) -> None:
        from textual.widgets import Input

        assert isinstance(event, Input.Submitted)
        value = event.value
        self.app.pop_screen()
        if callable(self.callback):
            self.callback(value)

    def key_escape(self) -> None:
        self.app.pop_screen()
        if callable(self.callback):
            self.callback(None)


class _FeedSelectScreen(Screen[str | None]):
    """Screen to select a feed to delete."""

    CSS = """
    _FeedSelectScreen {
        align: center middle;
    }
    #feed-select-dialog {
        width: 60;
        height: 20;
        padding: 1 2;
        background: $surface;
        border: tall $primary;
    }
    #feed-select-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #feed-list {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self, feed_urls: list[str], feed_titles: dict[str, str]) -> None:
        super().__init__()
        self.feed_urls = feed_urls
        self.feed_titles = feed_titles

    def compose(self) -> ComposeResult:
        with Vertical(id="feed-select-dialog"):
            yield Static("Select a feed to delete:", id="feed-select-title")
            yield OptionList(id="feed-list")

    def on_mount(self) -> None:
        list_widget = self.query_one("#feed-list", OptionList)
        for i, url in enumerate(self.feed_urls):
            title = self.feed_titles.get(url, url)
            prompt = Text()
            prompt.append(title, style="bold")
            prompt.append(f"\n{url}", style="dim italic")
            list_widget.add_option(Option(prompt, id=f"feed-{i}"))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        option_id = event.option.id
        if option_id and option_id.startswith("feed-"):
            idx = int(option_id.split("-", 1)[1])
            if 0 <= idx < len(self.feed_urls):
                url = self.feed_urls[idx]
                title = self.feed_titles.get(url, url)
                remove_feed_url(url)
                self.app.pop_screen()
                self.app.notify(f"Removed feed: {title}", severity="information")
                # Refresh the dashboard
                app = self.app
                if hasattr(app, "action_refresh"):
                    app.run_worker(app.action_refresh())

    def action_cancel(self) -> None:
        self.app.pop_screen()
