from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import (
    Footer,
    Header,
)
from rss_cli.view.articles.full_article import FullArticle


class ArticleScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield FullArticle("Full article")
        yield Footer()
