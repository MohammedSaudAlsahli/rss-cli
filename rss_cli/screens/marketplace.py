"""Marketplace screen — browse categories, search feeds, press Enter to subscribe."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    Input,
    OptionList,
    Static,
)
from textual.widgets.option_list import Option

from rss_cli.services.config import save_feed_url
from rss_cli.services.marketplace import (
    CATEGORIES,
    MarketplaceCategory,
    MarketplaceFeed,
    get_subscribed_urls,
    search_category,
    search_feeds,
)


class MarketplaceScreen(Screen[None]):
    """Browse and discover RSS feeds organized by category."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("s", "focus_search", "Search", show=True),
        Binding("backspace", "go_back_to_categories", "Categories", show=True),
    ]

    CSS = """
    MarketplaceScreen {
        layout: vertical;
    }
    #marketplace-search {
        height: 3;
        margin: 0 1;
    }
    #marketplace-search Input {
        width: 100%;
    }
    #marketplace-body {
        height: 1fr;
    }
    #category-list {
        width: 28;
        height: 1fr;
        border-right: solid $primary;
    }
    #category-list OptionList {
        height: 1fr;
    }
    #feed-panel {
        width: 1fr;
        height: 1fr;
    }
    #feed-list-container {
        height: 1fr;
    }
    #feed-list {
        height: 1fr;
    }
    #feed-detail {
        height: auto;
        max-height: 10;
        padding: 0 1;
        border-top: solid $primary;
    }
    #marketplace-status {
        height: 1;
        color: $text-disabled;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._categories: list[MarketplaceCategory] = CATEGORIES
        self._current_feeds: list[MarketplaceFeed] = []
        self._selected_category: MarketplaceCategory | None = None
        self._subscribed_urls: set[str] = set()
        self._search_mode = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            " [bold]RSS Marketplace[/] — browse categories or search for feeds",
            id="marketplace-header",
        )
        with Horizontal(id="marketplace-search"):
            yield Input(
                placeholder="Search feeds... (e.g. 'python', 'tech news', 'design')",
                id="search-input",
            )
        with Horizontal(id="marketplace-body"):
            with Vertical(id="category-list"):
                yield Static("  [bold]Categories[/]", id="cat-title")
                yield OptionList(id="cat-options")
            with Vertical(id="feed-panel"):
                with VerticalScroll(id="feed-list-container"):
                    yield OptionList(id="feed-list")
                yield Static("", id="feed-detail")
        yield Static(
            "  Select category or search · Enter to subscribe · Esc to go back",
            id="marketplace-status",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._subscribed_urls = get_subscribed_urls()
        self._populate_categories()
        cat_list = self.query_one("#cat-options", OptionList)
        cat_list.focus()
        if cat_list.option_count > 0:
            cat_list.highlighted = 0

    def _populate_categories(self) -> None:
        """Fill the category list."""
        cat_list = self.query_one("#cat-options", OptionList)
        cat_list.clear_options()
        for i, cat in enumerate(self._categories):
            prompt = Text()
            prompt.append(f" {cat.emoji} ", style="")
            prompt.append(cat.name, style="bold")
            cat_list.add_option(Option(prompt, id=f"cat-{i}"))

    def _populate_feeds(self, feeds: list[MarketplaceFeed]) -> None:
        """Fill the feed list with search results."""
        self._current_feeds = feeds
        feed_list = self.query_one("#feed-list", OptionList)
        feed_list.clear_options()

        self._subscribed_urls = get_subscribed_urls()

        if not feeds:
            feed_list.add_option(
                Option(
                    Text("No feeds found. Try a different search.", style="dim"),
                    id="empty-feeds",
                )
            )
            return

        for i, feed in enumerate(feeds):
            prompt = Text()
            if feed.url in self._subscribed_urls:
                prompt.append(" ✓ ", style="bold green")
            else:
                prompt.append(" + ", style="dim")
            title = feed.title
            if len(title) > 55:
                title = title[:52] + "..."
            prompt.append(title, style="bold white")
            if feed.subscribers > 0:
                sub_str = self._format_subscribers(feed.subscribers)
                prompt.append(f"  ({sub_str})", style="dim cyan")
            prompt.append("\n")
            desc = feed.description
            if len(desc) > 90:
                desc = desc[:87] + "..."
            prompt.append(f"  {desc}", style="dim")
            feed_list.add_option(Option(prompt, id=f"feed-{i}"))

        feed_list.focus()
        if feed_list.option_count > 0:
            feed_list.highlighted = 0
            self._show_feed_detail(0)

    @staticmethod
    def _format_subscribers(count: int) -> str:
        """Format subscriber count nicely."""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        if count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)

    def _show_feed_detail(self, idx: int) -> None:
        """Show detailed info for a feed in the detail panel."""
        if idx < 0 or idx >= len(self._current_feeds):
            return
        feed = self._current_feeds[idx]
        is_subbed = feed.url in self._subscribed_urls

        parts: list[str] = []
        if is_subbed:
            parts.append("[bold green]✓ Already subscribed[/]")
        else:
            parts.append("[dim]Press Enter to subscribe[/]")

        parts.append(f"\n[bold]{feed.title}[/]")
        if feed.description:
            parts.append(f"\n{feed.description}")
        if feed.website:
            parts.append(f"\n[dim]Website: {feed.website}[/]")
        if feed.language:
            parts.append(f" · [dim]{feed.language}[/]")
        parts.append(f"\n[dim]{feed.url}[/]")

        detail = self.query_one("#feed-detail", Static)
        detail.update(" ".join(parts))

    def _subscribe_to_highlighted_feed(self) -> None:
        """Subscribe to the currently highlighted feed in the feed list."""
        feed_list = self.query_one("#feed-list", OptionList)
        highlighted = feed_list.highlighted
        if highlighted is None or highlighted < 0:
            return
        if highlighted >= len(self._current_feeds):
            return

        feed = self._current_feeds[highlighted]

        # Check if already subscribed
        if feed.url in get_subscribed_urls():
            self.notify(
                f"Already subscribed: {feed.title}", severity="warning"
            )
            return

        if save_feed_url(feed.url):
            self._subscribed_urls.add(feed.url)
            self.notify(
                f"✓ Subscribed: {feed.title}", severity="information"
            )
            # Refresh the feed list to show ✓ indicator
            self._populate_feeds(self._current_feeds)
            # Keep highlight on the same item
            feed_list = self.query_one("#feed-list", OptionList)
            if highlighted < feed_list.option_count:
                feed_list.highlighted = highlighted
            self._show_feed_detail(highlighted)

            # Trigger a feed refresh in the main app
            app = self.app
            if hasattr(app, "action_refresh"):
                app.run_worker(app.action_refresh(force=True))

    # --- Event handlers ---

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle Enter press in category list (loads feeds) or feed list (subscribes)."""
        option_id = event.option.id
        if not option_id:
            return

        # Category selected — load feeds for that category
        if option_id.startswith("cat-"):
            idx = int(option_id.split("-", 1)[1])
            if 0 <= idx < len(self._categories):
                category = self._categories[idx]
                self._selected_category = category
                self._search_mode = False
                # Clear the search input
                search_input = self.query_one("#search-input", Input)
                search_input.value = ""
                # Update status
                status = self.query_one("#marketplace-status", Static)
                status.update(
                    f"  {category.emoji} {category.name} — loading feeds..."
                )
                # Show loading state
                feed_list = self.query_one("#feed-list", OptionList)
                feed_list.clear_options()
                feed_list.add_option(
                    Option(
                        Text("Loading...", style="dim italic"), id="loading"
                    )
                )
                # Fetch feeds in background
                self.run_worker(self._load_category_feeds(category))

        # Feed selected — subscribe!
        elif option_id.startswith("feed-"):
            self._subscribe_to_highlighted_feed()

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        """Update detail panel when highlight changes (arrow keys)."""
        option_id = event.option.id
        if option_id and option_id.startswith("feed-"):
            idx = int(option_id.split("-", 1)[1])
            self._show_feed_detail(idx)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        query = event.value.strip()
        if not query:
            return
        self._search_mode = True
        self._selected_category = None
        # Deselect category
        cat_list = self.query_one("#cat-options", OptionList)
        cat_list.highlighted = None
        # Update status
        status = self.query_one("#marketplace-status", Static)
        status.update(f'  Searching for "{query}"...')
        # Show loading
        feed_list = self.query_one("#feed-list", OptionList)
        feed_list.clear_options()
        feed_list.add_option(
            Option(Text("Searching...", style="dim italic"), id="loading")
        )
        self.run_worker(self._load_search_results(query))

    async def _load_category_feeds(
        self, category: MarketplaceCategory
    ) -> None:
        """Fetch feeds for a category and populate the list."""
        feeds = await search_category(category, limit=20)
        try:
            self._populate_feeds(feeds)
            status = self.query_one("#marketplace-status", Static)
            status.update(
                f"  {category.emoji} {category.name} — "
                f"{len(feeds)} feeds · Enter to subscribe · Esc to go back"
            )
        except Exception:
            pass

    async def _load_search_results(self, query: str) -> None:
        """Fetch search results and populate the list."""
        feeds = await search_feeds(query, limit=20)
        try:
            self._populate_feeds(feeds)
            status = self.query_one("#marketplace-status", Static)
            status.update(
                f'  Search: "{query}" — '
                f"{len(feeds)} feeds · Enter to subscribe · Esc to go back"
            )
        except Exception:
            pass

    # --- Actions ---

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_go_back_to_categories(self) -> None:
        """Return focus to category list."""
        cat_list = self.query_one("#cat-options", OptionList)
        cat_list.focus()

    def action_go_back(self) -> None:
        """Close the marketplace and return to dashboard."""
        self.app.pop_screen()
