from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from json import loads, dumps, JSONEncoder
from pathlib import Path
from typing import Any, Callable, cast
from webbrowser import open as open_url
from typing_extensions import Self

from pytz import UTC

from humanize import naturaltime

from textual.binding import Binding
from textual.reactive import var
from textual.widgets.option_list import Option, OptionDoesNotExist

from rich.console import Group, RenderableType
from rich.rule import Rule
from rich.table import Table

from rss_project.data.rss import rss_file
from rss_project.models.rss_model import RssData, RssCollection
from rss_project.widgets.extended_option_list import OptionListEx

#! the issue now is why articles class not showing articles!!!


class Article(Option):
    def __init__(self, data: RssData) -> None:
        self._data = data
        super().__init__(self.prompt, id=data.id)

    @property
    def tags(self) -> list[str]:
        return self._data.tags.split(", ")

    @property
    def prompt(self) -> Group:
        title = Table.grid(expand=True)
        title.add_column(ratio=1)
        title.add_column(justify="right")
        title.add_row(self._data.title)
        details = Table.grid(expand=True)
        details.add_column(ratio=1)
        details.add_column()
        details.add_row(
            f"[dim][i]{naturaltime(self._data.pub_date)}[/][/]",
            f"[dim]{', '.join(sorted(self.tags, key = str.casefold))}[/]",
        )
        return Group(title, details, Rule(style="dim"))

    def is_all(self, *checks: Callable[["Article"], bool]) -> bool:
        return all(check(self) for check in checks)

    def is_tagged(self, *tags: str) -> bool:
        return {tag.casefold() for tag in tags}.issubset(
            {tag.casefold() for tag in self.tags}
        )

    def has_text(self, search_text: str) -> bool:
        return (
            search_text.casefold()
            in (self._data.description + self._data.extended).casefold()
        )

    @classmethod
    def from_json(cls, data: list[dict[str, Any]]) -> "Article":
        for article in data:
            return cls(RssData(**article))

    @property
    def data(self) -> RssData:
        return self._data

    @data.setter
    def data(self, data: RssData) -> None:
        self._data = data
        self.set_prompt(self.prompt)


##############################################################################
class Articles(OptionListEx):
    DEFAULT_CSS = """
    Articles {
        scrollbar-gutter: stable;
    }

    Articles > .option-list--option {
        padding: 0 1 0 1;
    }
    """
    BINDINGS = [
        Binding("enter", "visit", "Visit"),
    ]
    articles: var[list[Article]] = var([], always_update=True, init=False)
    last_downloaded: var[datetime | None] = var(None)
    has_tags_filter: var[bool | None] = var(None, init=False)
    tag_filter: var[frozenset[str] | set[str]] = var(frozenset(), init=False)
    text_filter: var[str] = var("", init=False)

    @property
    def highlighted_article(self) -> Article | None:
        if self.highlighted is not None:
            return cast(Article, self.get_option_at_index(self.highlighted))
        return None

    def action_visit(self) -> None:
        if (article := self.highlighted_article) is not None:
            if article.data.link:
                open_url(article.data.link)

    @dataclass
    class Counts:
        all: int = 0
        untagged: int = 0
        tagged: int = 0

    @property
    def counts(self) -> Counts:
        counts = self.Counts(all=len(self.articles))

        for article in self.articles:
            if article.tags:
                counts.tagged += 1
            else:
                counts.untagged += 1
        return counts

    @property
    def tags(self) -> list[str]:
        tags: set[str] = set()
        for n in range(self.option_count):
            article = self.get_option_at_index(n)
            assert isinstance(article, Article)
            tags |= set(tag for tag in article.tags)
        return sorted(list(tags), key=str.casefold)

    @property
    def all_tags(self) -> list[str]:
        tags: set[str] = set()
        for article in self.articles:
            tags |= set(tag for tag in article.tags)
        return sorted(list(tags), key=str.casefold)

    @staticmethod
    def _tag_key(tag: tuple[str, int]) -> str:
        return tag[0].casefold()

    @property
    def tag_counts(self) -> list[tuple[str, int]]:
        tags: list[str] = []
        for n in range(self.option_count):
            article = self.get_option_at_index(n)
            assert isinstance(article, Article)
            tags.extend(article.tags)
        return sorted(list(Counter(tags).items()), key=self._tag_key)

    def _validate_tag_filter(
        self, new_value: frozenset[str] | set[str]
    ) -> frozenset[str]:
        """Ensure the tags filter always ends up being a frozen set."""
        return new_value if isinstance(new_value, frozenset) else frozenset(new_value)

    @property
    def as_json(self) -> dict[str, Any]:
        return {
            # "last_downloaded": None
            # if self.last_downloaded is None
            # else self.last_downloaded.isoformat(),
            "articles": [article.data.as_json for article in self.articles],
        }

    def load_json(self, data: dict[str, Any]) -> None:
        # self.last_downloaded = datetime.fromisoformat(data["last_downloaded"])
        self.articles = Article.from_json(data)

    #! this was the error
    def load(self) -> bool:
        file_path = rss_file()  # Specify the file path
        if Path(file_path).exists():  # Check if the file exists
            with open(file_path, "r", encoding="utf-8") as file:
                self.load_json(loads(file.read()))  # Load the JSON data

            return True
        return False

    class _Encoder(JSONEncoder):
        def default(self, o: object) -> Any:
            return datetime.isoformat(o) if isinstance(o, datetime) else o

    # def save(self) -> Self:
    #     rss_file().write_text(
    #         dumps(self.as_json, indent=4, cls=self._Encoder), encoding="utf-8"
    #     )
    #     return self

    async def download_all(self, collection: RssCollection) -> Self:
        self.articles = [
            Article(article) for article in await collection.all_articles()
        ]
        self.last_downloaded = datetime.now(UTC)
        return self

    @property
    def current_article(self) -> Article | None:
        if (article := self.highlighted) is None:
            return None
        return cast(Article, self.get_option_at_index(article))
