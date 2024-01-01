from webbrowser import open as open_url

from humanize import naturaltime

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import var
from textual.widgets import Label

from rss_project.widgets.articles import Article
from rss_project.widgets.tags import InlineTags


class Link(Label):
    class Visit(Message):
        """Message to indicate that the link should be visited."""

    def action_visit(self) -> None:
        """Handle a UI request to visit the link."""
        self.post_message(self.Visit())


class Details(VerticalScroll):
    DEFAULT_CSS = """
    Details {
        scrollbar-gutter: stable;
    }

    Details .hidden {
        visibility: hidden;
    }

    Details .empty {
        display: none;
    }

    Details Label {
        margin: 0 2 1 2;
        width: 1fr;
        color: $text;
    }

    Details #title {
        background: $primary;
        padding: 1 2 1 2;
        text-align: center;
    }

    Details .detail {
        background: $boost;
        padding: 1 2 1 2;
    }

    Details #added-ish {
        margin: 0 2 0 2;
        padding: 1 2 0 2;
    }

    Details #added-exact {
        margin: 0 2 1 2;
        padding: 0 2 1 2;
        text-align: right;
        color: $text-muted;
        text-style: italic;
    }

    Details InlineTags, Details InlineTags:focus {
        margin: 0 2 1 2;
    }
    """
    BINDINGS = [
        Binding("enter", "visit_article", "Visit"),
    ]
    article: var[Article | None] = var(None, always_update=True)

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Label(id="title")
        yield Label(id="description", classes="detail empty")
        yield Link(id="link", classes="detail")
        yield Label(id="added-ish", classes="detail")
        yield Label(id="added-exact", classes="detail")
        yield Label(id="is-read", classes="detail")
        yield Label(id="is-public", classes="detail")
        yield InlineTags(classes="empty")

    def _watch_article(self) -> None:
        try:
            if self.article is None:
                return
            self.query_one("#title", Label).update(self.article.data.title)
            self.query_one("#description", Label).update(self.article.data.description)
            self.query_one("#description", Label).set_class(
                not bool(self.article.data.description), "empty"
            )
            self.query_one(Link).update(f"[@click=visit]{self.article.data.link}[/]")
            self.query_one("#added-ish", Label).update(
                f"Added {naturaltime(self.article.data.pub_date)}"
            )
            self.query_one("#added-exact", Label).update(
                str(self.article.data.pub_date)
            )

            self.query_one(InlineTags).show(
                [(tag, 1) for tag in sorted(self.article.tags, key=str.casefold)]
            ).set_class(not bool(self.article.tags), "empty")

        finally:
            self.query("*").set_class(not bool(self.article), "hidden")

    @on(Link.Visit)
    def action_visit_article(self) -> None:
        """Visit the current bookmark, if there is one."""
        if self.article is not None:
            if self.article.data.link:
                open_url(self.article.data.link)
