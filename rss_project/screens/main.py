from functools import partial
from webbrowser import open as open_url

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Rule

from rss_project.screens.search import SearchInput
from rss_project.data.config import load_configuration, save_configuration
from rss_project.models.rss_model import RssCollection, RssData
from rss_project.widgets.articles import Articles, Article
from rss_project.widgets.details import Details
from rss_project.widgets.tags import TagsMenu
from rss_project.messages import (
    ClearTags,
    ShowAlsoTaggedWith,
    ShowTaggedWith,
)
from rss_project.data.rss import rss_file


class Main(Screen[None]):
    TITLE = f"rss cli"
    CSS = """
    Main {
        layout: horizontal;
    }

    Main > .focus {
        border: none;
        border-left: tall $accent 50%;
        background: $boost;
    }

    Main > .focus:focus, Main > .focus:focus-within {
        border: none;
        border-left: tall $accent;
        background: $panel;
    }

    #menu {
        padding: 0;
        margin: 0;
        width: 2fr;
        height: 1fr;
        min-width: 28;
    }

    #menu Filters {
        padding-left: 1;
    }

    #menu TagsMenu {
        height: 1fr;
    }

    #menu Rule {
        height: 1;
        margin: 0 0 0 0;
        background: $boost;
        color: $accent 50%;
    }

    #menu:focus-within Rule {
        background: $boost;
        color: $accent;
    }

    Articles {
        height: 1fr;
        width: 5fr;
    }

    Details {
        height: 1fr;
        width: 3fr;
        min-width: 30;
    }

    /* Tweaks to the above when the details are hidden. */

    Main.details-hidden Details {
        display: none;
    }

    Main.details-hidden Articles {
        width: 8fr;
    }
    """

    BINDINGS = [
        Binding("f1", "help", "Help"),
        Binding("f3", "toggle_details"),
        Binding("f4", "toggle_tag_order"),
        Binding("escape", "escape"),
        Binding("q", "quit", "Quit"),
        Binding("#", "focus('tags-menu')"),
        Binding("/", "search"),
    ]

    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu", classes="focus"):
            yield TagsMenu(id="tags-menu")
        yield Articles(classes="focus")
        yield Details(classes="focus")
        yield Footer()

    def on_mount(self) -> None:
        configuration = load_configuration()
        self.set_class(not configuration.details_visible, "details-hidden")
        self.sub_title = "Loading cached articles..."
        self.query_one(Articles).loading = True
        # self.query_one(TagsMenu).sort_by_count = configuration.sort_tags_by_count
        self.load_articles()

    @work(thread=True)
    def load_articles(self) -> None:
        self.query_one(Articles).load()

    @on(Articles.OptionHighlighted, "Articles")
    def refresh_details(self, event: Articles.OptionHighlighted) -> None:
        assert isinstance(event.option, Articles)
        self.query_one(Details).article = event.option

    # def action_help(self) -> None:
    #     """Show the help screen."""
    #     self.app.push_screen(Help(self))
    def action_toggle_details(self) -> None:
        self.toggle_class("details-hidden")
        config = load_configuration()
        config.details_visible = not self.has_class("details-hidden")
        save_configuration(config)

    def action_toggle_tag_order(self) -> None:
        tags = self.query_one(TagsMenu)
        tags.sort_by_count = not tags.sort_by_count
        tags.show(self.query_one(Articles).tag_counts)
        config = load_configuration()
        config.sort_tags_by_count = tags.sort_by_count
        save_configuration(config)

    def action_escape(self) -> None:
        if self.screen.focused is None:
            return
        if isinstance(self.screen.focused, Details) or isinstance(
            self.screen.focused.parent, Details
        ):
            self.query_one(Articles).focus()

    def _search(self, search_text: str) -> None:
        self.query_one(Articles).text_filter = search_text

    def action_search(self) -> None:
        self.app.push_screen(SearchInput(), callback=self._search)

    @on(ShowTaggedWith)
    def show_tagged_with(self, event: ShowTaggedWith) -> None:
        self.query_one(Articles).tag_filter = {event.tag}

    @on(ShowAlsoTaggedWith)
    def show_also_tagged_with(self, event: ShowAlsoTaggedWith) -> None:
        """Add a tag to any current tag filter and show the matching bookmarks.

        Args:
            event: The event that contains the tag to add.
        """
        self.query_one(Articles).tag_filter |= {event.tag}
