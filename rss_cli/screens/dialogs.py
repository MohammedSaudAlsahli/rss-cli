"""Dialog screens for RSS CLI (input and feed selection)."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from rss_cli.services.config import remove_feed_url


class InputScreen(Screen[None]):
    """Simple input dialog screen."""

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


class FeedSelectScreen(Screen[str | None]):
    """Screen to select a feed to delete."""

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
                app = self.app
                if hasattr(app, "action_refresh"):
                    app.run_worker(app.action_refresh())

    def action_cancel(self) -> None:
        self.app.pop_screen()
