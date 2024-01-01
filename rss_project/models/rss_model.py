from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import reduce
from hashlib import md5
from uuid import uuid4
from json import loads
from operator import or_
from typing_extensions import Final
import feedparser
from pytz import UTC
from json import dump

from rss_project.data.rss import rss_file


def parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.removesuffix("Z") + "+00:00")


@dataclass
class RssData:
    id: str
    provider: str
    title: str
    description: str
    content: list[str]
    link: str
    pub_date: str
    author: str
    authors: list[str]
    tags: str

    @classmethod
    def from_entry(cls, entry, provider):
        return cls(
            id=uuid4().hex,
            provider=provider,
            title=entry.title,
            description=entry.description,
            content=[
                content.get("value", "no content")
                for content in entry.get("content", [])
            ],
            link=entry.links[0].get("href") if entry.links else None,
            pub_date=entry.published,
            author=entry.get("author"),
            authors=entry.get("author", []),
            # tags=[tag.term for tag in entry.get("tags", [])],
            tags=", ".join(tag.term for tag in entry.get("tags", [])),
        ).__dict__

    @property
    def as_json(self) -> dict[str, str]:
        return asdict(self)


# ------------------------------------------------------------------------------


class RssCollection:
    class Error(Exception):
        ...

    class RssError(Error):
        ...

    def __init__(self) -> None:
        self._all_cache: list[RssData] = []
        self._last_request: datetime | None = None

    # Todo: if everything was right I will change this to a list of rss feeds that user add
    def _rss_feeds(self) -> list[str]:
        return ["https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"]

    # Todo: in the future I need to refactor this for youtube and twitter feature
    def _rss_parser(self) -> list[RssData]:
        path = rss_file()
        articles: list[RssData] = []
        for url in self._rss_feeds():
            feed = feedparser.parse(url)
            if feed.status == 200:
                for entry in feed.entries:
                    article = RssData.from_entry(entry, feed.channel.title)
                    articles.append(article)
        with open(path, "w") as outfile:
            dump(articles, outfile)
        return articles

    _LIMIT: Final[timedelta] = timedelta(minutes=15)

    async def all_articles(self) -> list[RssData]:
        self._all_cache = [
            RssData.from_entry(article) for article in loads(await self._rss_parser())
        ]
        self._last_all = datetime.now(UTC)
        return self._all_cache

    def _request_limit(self) -> bool:
        if self._last_request is None:
            return False
        elif (datetime.now() - self._last_request) > self._LIMIT:
            return False
        else:
            True


if __name__ == "__main__":
    RssCollection()._rss_parser()
