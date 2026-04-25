"""Dashboard — source-filtered tabs left (1fr), preview right (2fr)."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, OptionList, Static, TabbedContent, TabPane
from textual.widgets.option_list import Option, OptionDoesNotExist

from rss_cli.models.article import Article, Feed, FeedType
from rss_cli.screens.dialogs import FeedSelectScreen, InputScreen
from rss_cli.services.cache import (
    apply_all_state,
    invalidate_state_cache,
    mark_article_read,
    toggle_bookmark,
)
from rss_cli.services.config import load_feed_urls, save_feed_url

# Mapping of tab ID → FeedType filter (None = all sources)
_TAB_FEED_TYPES: dict[str, FeedType | None] = {
    "all-tab": None,
    "rss-tab": FeedType.RSS,
    "reddit-tab": FeedType.REDDIT,
    "twitter-tab": FeedType.TWITTER,
}

# Number of articles shown initially and per "load more" batch
_PAGE_SIZE = 25


class DashboardScreen(Screen[None]):
    """Main dashboard: source tabs left, preview right."""

    BINDINGS = [
        Binding("b", "toggle_bookmark", "Bookmark", show=True),
        Binding("o", "open_browser", "Browser", show=True),
        Binding("enter", "read_article", "Read", show=True),
        Binding("s", "search", "Search", show=True),
        Binding("a", "add_feed", "Add feed", show=True),
        Binding("m", "marketplace", "Marketplace", show=True),
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
        self._search_query: str = ""
        # Track how many articles are currently displayed per list
        self._displayed: dict[str, int] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            with Vertical(id="article-panel"):
                with TabbedContent(id="left-tabs"):
                    with TabPane("All", id="all-tab"):
                        yield OptionList(id="all-list")
                    with TabPane("RSS", id="rss-tab"):
                        yield OptionList(id="rss-list")
                    with TabPane("Reddit", id="reddit-tab"):
                        yield OptionList(id="reddit-list")
                    with TabPane("Twitter", id="twitter-tab"):
                        yield OptionList(id="twitter-list")
                    with TabPane("Bookmarks", id="bookmarks-tab"):
                        yield OptionList(id="bookmarks-list")
            with Vertical(id="right-panel"):
                yield Static("", id="preview-title")
                yield Static("", id="preview-meta")
                with VerticalScroll(id="preview-scroll"):
                    yield Markdown("", id="preview-content")
        yield Footer()

    def on_mount(self) -> None:
        self._populate_all_lists()
        # Focus the all-list and highlight the first item
        list_widget = self.query_one("#all-list", OptionList)
        list_widget.focus()
        if list_widget.option_count > 0:
            list_widget.highlighted = 0

    def refresh_state(self) -> None:
        """Re-apply read/bookmark state from disk and repopulate lists."""
        invalidate_state_cache()
        apply_all_state(self.all_articles)
        self._populate_all_lists()

    def update_feeds(self, feeds: list[Feed]) -> None:
        self.feeds = feeds
        self.all_articles = []
        for feed in feeds:
            self.all_articles.extend(feed.articles)
        apply_all_state(self.all_articles)
        self._filtered_articles = list(self.all_articles)
        self._search_query = ""
        self._populate_all_lists()

    # --- Article filtering helpers ---

    def _articles_for_tab(self, tab_id: str) -> list[Article]:
        """Return articles matching the tab's source filter, respecting search."""
        feed_type = _TAB_FEED_TYPES.get(tab_id)
        base = self._filtered_articles if self._search_query else self.all_articles
        if feed_type is None:
            return base
        return [a for a in base if a.feed_type == feed_type]

    def _list_id_for_tab(self, tab_id: str) -> str:
        """Map tab ID to its OptionList widget ID."""
        return f"{tab_id.replace('-tab', '')}-list" if tab_id != "all-tab" else "all-list"

    # --- Display helpers ---

    def _make_meta_line(self, article: Article) -> str:
        """Build the second line: date · rss_name · feed_title."""
        parts = [article.pub_date_display, article.feed_name, article.feed_title]
        return " · ".join(parts)

    def _make_article_prompt(self, article: Article, index: int, total: int) -> Text:
        """Build a two-line Rich Text prompt: index + title + meta."""
        title_text = article.title
        if len(title_text) > 70:
            title_text = title_text[:67] + "..."
        title_style = "dim" if article.is_read else "bold white"
        cell = Text()
        cell.append(f"{index + 1:>3}/{total} ", style="dim")
        if article.is_bookmarked:
            cell.append("• ", style="bold cyan")
        cell.append(title_text, style=title_style)
        cell.append("\n")
        cell.append(self._make_meta_line(article), style="dim")
        return cell

    def _make_bookmark_prompt(self, article: Article, index: int, total: int) -> Text:
        """Build a two-line Rich Text prompt for bookmarks: index + title + meta."""
        title_text = article.title
        if len(title_text) > 50:
            title_text = title_text[:47] + "..."
        title_style = "dim" if article.is_read else "bold white"
        cell = Text()
        cell.append(f"{index + 1:>3}/{total} ", style="dim")
        cell.append("• ", style="bold cyan")
        cell.append(title_text, style=title_style)
        cell.append("\n")
        cell.append(self._make_meta_line(article), style="dim")
        return cell

    def _make_load_more_prompt(self, shown: int, total: int) -> Text:
        """Build the 'Load more' option prompt."""
        remaining = total - shown
        prompt = Text()
        prompt.append(
            f"  ↓ Load more ({remaining} remaining)...",
            style="bold cyan",
        )
        return prompt

    # --- List population ---

    def _populate_source_list(self, list_id: str, articles: list[Article]) -> None:
        """Populate an OptionList with the first page of articles."""
        list_widget = self.query_one(f"#{list_id}", OptionList)
        list_widget.clear_options()

        total = len(articles)
        # Reset display count to one page
        self._displayed[list_id] = min(_PAGE_SIZE, total)

        if not articles:
            label = list_id.replace("-list", "").upper()
            if list_id == "all-list":
                empty_msg = "No articles yet. Press [r] to refresh or [a] to add a feed."
            else:
                empty_msg = f"No {label} articles. Press [a] to add a feed."
            list_widget.add_option(
                Option(Text(empty_msg, style="dim"), id="empty")
            )
            return

        shown = self._displayed[list_id]
        for i in range(shown):
            article = articles[i]
            list_widget.add_option(
                Option(
                    self._make_article_prompt(article, i, total),
                    id=f"{list_id}-article-{i}",
                )
            )

        # Add "load more" if there are remaining articles
        if shown < total:
            list_widget.add_option(
                Option(
                    self._make_load_more_prompt(shown, total),
                    id=f"{list_id}-load-more",
                )
            )

    def _load_more(self, list_id: str) -> None:
        """Append the next page of articles to the list."""
        tab_map = {
            "all-list": "all-tab",
            "rss-list": "rss-tab",
            "reddit-list": "reddit-tab",
            "twitter-list": "twitter-tab",
        }
        tab_id = tab_map.get(list_id)
        if not tab_id:
            return
        articles = self._articles_for_tab(tab_id)
        total = len(articles)
        current = self._displayed.get(list_id, 0)

        if current >= total:
            return

        list_widget = self.query_one(f"#{list_id}", OptionList)

        # Remove the old "load more" option if present
        try:
            list_widget.remove_option(f"{list_id}-load-more")
        except (OptionDoesNotExist, Exception):
            pass

        # Add the next page
        next_count = min(current + _PAGE_SIZE, total)
        for i in range(current, next_count):
            article = articles[i]
            list_widget.add_option(
                Option(
                    self._make_article_prompt(article, i, total),
                    id=f"{list_id}-article-{i}",
                )
            )

        self._displayed[list_id] = next_count

        # Add new "load more" if still remaining
        if next_count < total:
            list_widget.add_option(
                Option(
                    self._make_load_more_prompt(next_count, total),
                    id=f"{list_id}-load-more",
                )
            )

        # Keep focus and highlight on the next unread article
        list_widget.focus()
        if current < list_widget.option_count:
            list_widget.highlighted = current

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

        total = len(bookmarked)
        for i, article in enumerate(bookmarked):
            list_widget.add_option(
                Option(
                    self._make_bookmark_prompt(article, i, total),
                    id=f"bookmark-{i}",
                )
            )

    def _populate_all_lists(self) -> None:
        """Populate all source tabs + bookmarks."""
        for tab_id in _TAB_FEED_TYPES:
            list_id = self._list_id_for_tab(tab_id)
            articles = self._articles_for_tab(tab_id)
            self._populate_source_list(list_id, articles)
        self._populate_bookmarks()

    # --- Preview ---

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

    # --- In-place option updates ---

    def _update_article_option_in_list(
        self, list_id: str, articles: list[Article], article: Article
    ) -> None:
        """Update a single article option in a specific list."""
        total = len(articles)
        shown = self._displayed.get(list_id, _PAGE_SIZE)
        for i, a in enumerate(articles[:shown]):
            if a.link == article.link:
                list_widget = self.query_one(f"#{list_id}", OptionList)
                try:
                    list_widget.replace_option_prompt(
                        f"{list_id}-article-{i}",
                        self._make_article_prompt(article, i, total),
                    )
                except OptionDoesNotExist:
                    pass
                break

    def _update_article_in_all_lists(self, article: Article) -> None:
        """Update an article's prompt in all source tabs where it appears."""
        for tab_id in _TAB_FEED_TYPES:
            articles = self._articles_for_tab(tab_id)
            list_id = self._list_id_for_tab(tab_id)
            self._update_article_option_in_list(list_id, articles, article)

    def _update_bookmark_options_for_read(self, article: Article) -> None:
        """Update bookmark list entries for an article that was marked read."""
        bm_widget = self.query_one("#bookmarks-list", OptionList)
        bookmarked = [a for a in self.all_articles if a.is_bookmarked]
        total = len(bookmarked)
        for i, bm_article in enumerate(bookmarked):
            if bm_article.link == article.link:
                try:
                    bm_widget.replace_option_prompt(
                        f"bookmark-{i}",
                        self._make_bookmark_prompt(bm_article, i, total),
                    )
                except OptionDoesNotExist:
                    pass
                break

    # --- Active article retrieval ---

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
            list_id = self._list_id_for_tab(active_tab)
            articles = self._articles_for_tab(active_tab)
            shown = self._displayed.get(list_id, _PAGE_SIZE)
            list_widget = self.query_one(f"#{list_id}", OptionList)
            highlighted = list_widget.highlighted
            if highlighted is None or highlighted < 0 or highlighted >= shown:
                return None
            return articles[highlighted]

    # --- Selection handlers ---

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection in any article list or bookmarks list."""
        option_id = event.option.id
        if not option_id or option_id.startswith("empty"):
            return

        # "Load more" selected — append next page
        if option_id.endswith("-load-more"):
            list_id = option_id.replace("-load-more", "")
            self._load_more(list_id)
            return

        if option_id.startswith("bookmark-"):
            bookmarked = [a for a in self.all_articles if a.is_bookmarked]
            idx = int(option_id.split("-", 1)[1])
            if 0 <= idx < len(bookmarked):
                article = bookmarked[idx]
                if not article.is_read:
                    mark_article_read(article.link)
                    article.is_read = True
                    self._update_article_in_all_lists(article)
                    # Update the bookmark entry in-place
                    bm_widget = self.query_one("#bookmarks-list", OptionList)
                    try:
                        bm_widget.replace_option_prompt(
                            f"bookmark-{idx}",
                            self._make_bookmark_prompt(
                                article, idx, len(bookmarked)
                            ),
                        )
                    except OptionDoesNotExist:
                        pass
                self._update_preview(article)
            return

        # Source list articles: option ID is "{list_id}-article-{idx}"
        if "-article-" in option_id:
            # Extract the list ID prefix and index
            parts = option_id.rsplit("-article-", 1)
            if len(parts) == 2:
                list_id = parts[0]
                idx = int(parts[1])
                # Find which tab this list belongs to
                articles = self._articles_for_list_id(list_id)
                if articles and 0 <= idx < len(articles):
                    article = articles[idx]
                    if not article.is_read:
                        mark_article_read(article.link)
                        article.is_read = True
                        self._update_article_in_all_lists(article)
                        self._update_bookmark_options_for_read(article)
                    self._update_preview(article)

    def _articles_for_list_id(self, list_id: str) -> list[Article]:
        """Map a list widget ID back to its filtered articles."""
        tab_map = {
            "all-list": "all-tab",
            "rss-list": "rss-tab",
            "reddit-list": "reddit-tab",
            "twitter-list": "twitter-tab",
        }
        tab_id = tab_map.get(list_id)
        if tab_id:
            return self._articles_for_tab(tab_id)
        return self._filtered_articles

    def _find_article_index_in_list(self, list_id: str, article: Article) -> int | None:
        """Find the index of an article in a specific list."""
        articles = self._articles_for_list_id(list_id)
        for i, a in enumerate(articles):
            if a.link == article.link:
                return i
        return None

    # --- Actions ---

    def action_read_article(self) -> None:
        article = self._get_active_article()
        if article is None:
            self.notify("No article selected", severity="warning")
            return
        mark_article_read(article.link)
        article.is_read = True
        self._update_article_in_all_lists(article)
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
        self._update_article_in_all_lists(article)
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

    def action_marketplace(self) -> None:
        """Open the RSS marketplace to discover and subscribe to feeds."""
        app = self.app
        if hasattr(app, "go_to_marketplace"):
            app.go_to_marketplace()

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
        self._search_query = ""
        self._filtered_articles = list(self.all_articles)
        self._populate_all_lists()

    def action_search(self) -> None:
        def _on_result(result: str | None) -> None:
            if result is None:
                return
            query = result.strip().lower()
            if not query:
                self._search_query = ""
                self._filtered_articles = list(self.all_articles)
            else:
                self._search_query = query
                self._filtered_articles = [
                    a
                    for a in self.all_articles
                    if query in a.title.lower()
                    or query in a.description.lower()
                    or query in a.author.lower()
                    or query in a.feed_title.lower()
                ]
            self._populate_all_lists()

        self.app.push_screen(InputScreen("Search articles:", _on_result))
