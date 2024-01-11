from typing import Type
from textual._path import CSSPathType
from textual.driver import Driver
from textual.widgets import OptionList
from textual.widgets.option_list import Option, OptionDoesNotExist
from textual.app import App, CSSPathType, ComposeResult
from rich.table import Table
from rich.console import Group
from datetime import datetime

from rss_project.models.rss_model import RssCollection, RssData


class Main(App):
    def __init__(self):
        super().__init__()
        self._load = self.load_feeds()
        self._rss_collection = RssCollection()._rss_parser()

    def compose(self) -> ComposeResult:
        feeds = self.feeds()
        yield from (OptionList(feed) for feed in feeds)

    def load_feeds(self) -> list[RssData]:
        RssCollection()._rss_parser()
        all_feeds = RssCollection()._read_rss()
        return all_feeds

    def feeds(self) -> list:
        def sort_by_pub_date(feed: RssData):
            return datetime.strptime(feed.pub_date, "%a, %d %b %Y %H:%M:%S %z")

        feeds = sorted(self._load, key=sort_by_pub_date)
        all_feeds: list[Group] = []
        for feed in feeds:
            title = Table.grid(expand=True)
            title.add_column(ratio=1)
            title.add_column(justify="right")
            title.add_row(feed.title)

            details = Table.grid(expand=True)
            details.add_column(ratio=1)
            details.add_row(f"\n[dim]{feed.pub_date}[/]\n[dim]{feed.tags}[/]")
            Option(all_feeds.append(Group(title, details)))

        return all_feeds


if __name__ == "__main__":
    Main().run()
