from textual import on, log
from textual.app import ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import Footer

from feed_list import RssList
from feed_details import FeedDetails


class FeedsScreen(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.details = FeedDetails()

    def compose(self) -> ComposeResult:
        yield RssList(id="rss-list")
        yield self.details
        yield Footer()

    @on(RssList.RssOpened)
    # ! error on on_rss_opened method
    def on_rss_opened(self, event: RssList.RssOpened) -> None:
        log.debug(f"Feed selected from rss list: {event.feed.id}")
        feed_widget = self.query_one(FeedDetails)
        opened_feed = RssList().get_feed_by_id(event.feed.id)
        log.debug(
            f"Retrieved feed {opened_feed.id!r} "
            f"containing {len(opened_feed.content)} messages from database."
        )


if __name__ == "__main__":
    f = RssList().all_feeds()
    for feed in f:
        print(feed.id)
