from rss_cli.utils.default_config import BINDINGS
from rss_cli.view.css.main import SCREEN_STYLE
from rss_cli.view.screens.quit_screen import QuitScreen
from rss_cli.view.screens.article_screen import ArticleScreen
from rss_cli.view.screens.main_screen import MainScreen
from textual.app import App


class RssCli(App):
    BINDINGS = BINDINGS
    CSS = SCREEN_STYLE
    SCREENS = {
        "main": MainScreen(),
        "help": ...,
        "test": ArticleScreen,
    }

    def on_ready(self) -> None:
        self.push_screen("main")

    def action_dark_mode(self):
        self.dark = not self.dark

    def action_update_rss(self):
        ...

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())


if __name__ == "__main__":
    app = RssCli().run()
