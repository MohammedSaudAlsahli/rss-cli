from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import var
from textual.widgets import Label

from rss_project.models import RssData, RssCollection


class FeedDetails(VerticalScroll):
    # DEFAULT_CSS = """
    # Details {
    #     scrollbar-gutter: stable;

    #     .hidden {
    #         visibility: hidden;
    #     }

    #     .empty {
    #         display: none;
    #     }

    #     Label {
    #         margin: 0 2 1 2;
    #         width: 1fr;
    #         color: $text;
    #     }

    #     #title {
    #         background: $primary;
    #         padding: 1 2 1 2;
    #         text-align: center;
    #     }

    #     .detail {
    #         background: $boost;
    #         padding: 1 2 1 2;
    #     }

    #     #link {
    #         margin: 0 2 0 2;
    #         padding: 1 2 0 2;
    #     }

    #     #pub_date {
    #         margin: 0 2 1 2;
    #         padding: 0 2 1 2;
    #         text-align: right;
    #         color: $text-muted;
    #         text-style: italic;
    #     }
    # }
    # """
    feed: var[RssData | None] = var(None, always_update=True)

    def compose(self) -> ComposeResult:
        yield Label(id="title")
        yield Label(id="description", classes="detail empty")
        # yield Link(id="link", classes="detail")
        yield Label(id="link", classes="detail")
        yield Label(id="pub_date", classes="detail")
        # yield Label(id="is-read", classes="detail")
        # yield Label(id="is-public", classes="detail")
        # yield InlineTags(classes="empty")

    def _watch_feed(self):
        try:
            if self.feed is None:
                return
            self.query_one("#title", Label).update(self.feed.title)
            self.query_one("#description", Label).update(self.feed.description)
            self.query_one("#added-ish", Label).update(f"Added at {self.feed.pub_date}")
            self.query_one("#link", Label).update(self.feed.link)

        finally:
            self.query("*").set_class(not bool(self.feed), "hidden")
