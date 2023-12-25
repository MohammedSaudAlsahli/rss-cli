from textual.screen import Screen
from textual.app import ComposeResult
from rss_cli.view.articles.articles_grid import ArticlesGrid
from textual.widgets import (
    Footer,
    Header,
)


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ArticlesGrid()
        yield Footer()
