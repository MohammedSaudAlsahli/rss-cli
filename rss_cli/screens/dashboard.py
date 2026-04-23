"""Dashboard — articles/bookmarks left (1fr), preview right (2fr)."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, OptionList, Static, TabbedContent, TabPane
from textual.widgets.option_list import Option, OptionDoesNotExist

from rss_cli.models.article import Article, Feed
from rss_cli.screens.dialogs import FeedSelectScreen, InputScreen
from rss_cli.services.cache import (
    apply_all_state,
    invalidate_state_cache,
    mark_article_read,
    toggle_bookmark,
)
from rss_cli.services.config import load_feed_urls, save_feed_url


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
        invalidate_state_cache()
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

        # Use cached parsed content instead of running html_to_text every time
        parsed = article.parsed_content
        if parsed:
            content_parts.append(parsed)

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

    def _update_article_option(self, idx: int) -> None:
        """Update a single article option in-place without rebuilding the list."""
        if idx < 0 or idx >= len(self._filtered_articles):
            return
        article = self._filtered_articles[idx]
        list_widget = self.query_one("#article-list", OptionList)
        try:
            list_widget.replace_option_prompt(
                f"article-{idx}",
                self._make_article_prompt(article),
            )
        except OptionDoesNotExist:
            pass  # List may have been rebuilt; fall back to full populate

    def _update_bookmark_options_for_read(self, article: Article) -> None:
        """Update bookmark list entries for an article that was marked read."""
        bm_widget = self.query_one("#bookmarks-list", OptionList)
        bookmarked = [a for a in self.all_articles if a.is_bookmarked]
        for i, bm_article in enumerate(bookmarked):
            if bm_article.link == article.link:
                try:
                    bm_widget.replace_option_prompt(
                        f"bookmark-{i}",
                        self._make_bookmark_prompt(bm_article),
                    )
                except OptionDoesNotExist:
                    pass
                break

    def _get_active_article(self) -> Article | None:
        """Return the currently highlighted article, regardless of which tab is active."""
        tabs = self.query_one("#left-tabs", TabbedContent)
        active_tab = tabs.active

        if active_tab == "bookmarks-tab":
            bm_widget = self.query_one("#bookmarks-list", OptionList)
            highlighted = bm_widget.highlighted
            if highlighted is None or highlighted < 0:
                return None
            bookmarked = [a for a in self.all_articles if a.is_bookmarked]
            if highlighted < len(bookmarked):
                return bookmarked[highlighted]
            return None
        else:
            list_widget = self.query_one("#article-list", OptionList)
            highlighted = list_widget.highlighted
            if (
                highlighted is None
                or highlighted < 0
                or highlighted >= len(self._filtered_articles)
            ):
                return None
            return self._filtered_articles[highlighted]

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection in either the article list or bookmarks list."""
        option_id = event.option.id
        if option_id and option_id.startswith("article-"):
            idx = int(option_id.split("-", 1)[1])
            if 0 <= idx < len(self._filtered_articles):
                article = self._filtered_articles[idx]
                if not article.is_read:
                    mark_article_read(article.link)
                    article.is_read = True
                    # Lazy update: only refresh the changed option, not the whole list
                    self._update_article_option(idx)
                    self._update_bookmark_options_for_read(article)
                self._update_preview(article)
        elif option_id and option_id.startswith("bookmark-"):
            bookmarked = [a for a in self.all_articles if a.is_bookmarked]
            idx = int(option_id.split("-", 1)[1])
            if 0 <= idx < len(bookmarked):
                article = bookmarked[idx]
                if not article.is_read:
                    mark_article_read(article.link)
                    article.is_read = True
                    # Lazy update: update the article in the main list
                    art_idx = self._find_article_index(article)
                    if art_idx is not None:
                        self._update_article_option(art_idx)
                    # Update the bookmark entry in-place
                    bm_widget = self.query_one("#bookmarks-list", OptionList)
                    try:
                        bm_widget.replace_option_prompt(
                            f"bookmark-{idx}",
                            self._make_bookmark_prompt(article),
                        )
                    except OptionDoesNotExist:
                        pass
                self._update_preview(article)

    def _find_article_index(self, article: Article) -> int | None:
        """Find the index of an article in _filtered_articles by link."""
        for i, a in enumerate(self._filtered_articles):
            if a.link == article.link:
                return i
        return None

    def action_read_article(self) -> None:
        article = self._get_active_article()
        if article is None:
            self.notify("No article selected", severity="warning")
            return
        mark_article_read(article.link)
        article.is_read = True
        # Lazy update: refresh the article option in the main list
        art_idx = self._find_article_index(article)
        if art_idx is not None:
            self._update_article_option(art_idx)
        self._update_bookmark_options_for_read(article)

        app = self.app
        if hasattr(app, "go_to_reader"):
            app.go_to_reader(article)

    def action_toggle_bookmark(self) -> None:
        article = self._get_active_article()
        if article is None:
            self.notify("No article selected", severity="warning")
            return
        is_bookmarked = toggle_bookmark(article.link)
        article.is_bookmarked = is_bookmarked
        label = "Bookmarked" if is_bookmarked else "Bookmark removed"
        self.notify(label, severity="information")
        # Lazy update: refresh the article option in the main list
        art_idx = self._find_article_index(article)
        if art_idx is not None:
            self._update_article_option(art_idx)
        # Bookmarks list must be fully rebuilt (set of bookmarked articles changed)
        self._populate_bookmarks()
        # Re-focus the bookmarks list and restore a sensible highlight position
        tabs = self.query_one("#left-tabs", TabbedContent)
        if tabs.active == "bookmarks-tab":
            bm_widget = self.query_one("#bookmarks-list", OptionList)
            bm_widget.focus()
            if bm_widget.option_count > 0:
                bm_widget.highlighted = 0
        if self._selected_article and self._selected_article.link == article.link:
            self._update_preview(article)

    def action_open_browser(self) -> None:
        import webbrowser

        article = self._get_active_article()
        if article is None:
            self.notify("No article selected", severity="warning")
            return
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

        self.app.push_screen(InputScreen("Enter RSS feed URL:", _on_result))

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
        self.app.push_screen(FeedSelectScreen(feed_urls, feed_titles))

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

        self.app.push_screen(InputScreen("Search articles:", _on_result))
