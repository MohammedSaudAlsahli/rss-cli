from dataclasses import dataclass

from rich.console import RenderResult, Console, ConsoleOptions
from rich.padding import Padding
from rich.text import Text
from textual import log, on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from rss_project.models import RssData, RssCollection


@dataclass
class RssListItemRenderable:
    feed: RssData
    is_open: bool = False

    def __rich__(self, console: Console, option: ConsoleOptions) -> RenderResult:
        yield Padding(
            Text.assemble(
                (self.feed.title, "" if not self.is_open else "b"),
                "\n",
                self.feed.pub_date,
            ),
            pad=(0, 1),
            style="reverse" if self.is_open else "",
        )


class RssListItem(Option):
    def __init__(self, feed: RssData, is_open: bool = False) -> None:
        super().__init__(RssListItemRenderable(feed, is_open))
        self.feed = feed
        self.is_open = is_open


class RssList(Widget):
    current_feed_id: reactive[str | None] = reactive(None)
    COMPONENT_CLASSES = {"app-title", "app-subtitle"}

    @dataclass
    class RssOpened(Message):
        feed: RssData

    def compose(self) -> ComposeResult:
        with Vertical(id="cl-header-container"):
            yield Static(
                Text("rss-cli", style=self.get_component_rich_style("app-title"))
            )
            yield Static(
                Text(
                    "Rss feeds in terminal",
                    style=self.get_component_rich_style("app-subtitle"),
                )
            )
        self.options = self.load_rss_list_items()
        option_list = OptionList(
            *self.options,
            id="cl-option-list",
        )
        yield option_list

    @on(OptionList.OptionSelected, "#cl-option-list")
    def post_feed_opened(self, event: OptionList.OptionSelected) -> None:
        assert isinstance(event.option, RssListItem)
        feed = event.option.feed
        self.current_feed_id = feed.id
        self.reload_and_refresh()
        self.post_message(RssList.RssOpened(feed=feed))

    def on_focus(self) -> None:
        log.debug("Sidebar focused")
        self.query_one("#cl-option-list", OptionList).focus()

    def reload_and_refresh(self, new_highlighted: int = -1) -> None:
        self.options = self.load_rss_list_items()
        option_list = self.query_one(OptionList)
        old_highlighted = option_list.highlighted
        option_list.clear_options()
        option_list.add_options(self.options)
        if new_highlighted > -1:
            option_list.highlighted = new_highlighted
        else:
            option_list.highlighted = old_highlighted

    def load_rss_list_items(self):
        feeds = self.all_feeds()
        return [
            RssListItem(feed, is_open=self.current_feed_id == feed.id) for feed in feeds
        ]

    def all_feeds(self) -> list[RssData]:
        RssCollection()._rss_parser()
        all_feeds = RssCollection()._read_rss()
        return all_feeds

    def get_feed_by_id(self, feed_id: str) -> RssData | None:
        feeds = self.all_feeds()
        for feed in feeds:
            if feed.id == feed_id:
                return feed
        return None


if __name__ == "__main__":
    f = RssList().load_rss_list_items()
    for index, rss in enumerate(f):
        print(index, rss.feed.id)

    print("-" * 50)
    f = RssCollection()._read_rss()
    for index, i in enumerate(f):
        print(index, i.id)
