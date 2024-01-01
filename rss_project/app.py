import os

from textual.app import App
from textual.binding import Binding

from rss_project.screens import Main
from rss_project.data import load_configuration, save_configuration


class RssCli(App):
    BINDINGS = [
        Binding("ctrl+backslash", "gndn"),
        Binding("ctrl+p", "command_palette", priority=True),
    ]

    def __init__(self) -> None:
        """Initialise the application."""
        super().__init__()
        self.dark = load_configuration().dark_mode

    def on_mount(self) -> None:
        self.push_screen(Main())

    def _watch_dark(self) -> None:
        """Save the light/dark mode configuration choice."""
        configuration = load_configuration()
        configuration.dark_mode = self.dark
        save_configuration(configuration)


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    RssCli().run()
