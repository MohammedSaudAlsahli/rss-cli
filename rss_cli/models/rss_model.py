from dataclasses import dataclass
from datetime import datetime
from json import dump, load

import feedparser

from ..data import rss_file, RSS_FEEDS


@dataclass
class RssData:
    provider: str
    title: str
    description: str
    content: list[str]
    link: str
    pub_date: str
    author: str
    tags: list[str]

    @classmethod
    def from_entry(cls, entry, provider):
        return cls(
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
            tags=[tag.term for tag in entry.get("tags", [])],
        )


class RssCollection:
    # Todo: in the future I need to refactor this for youtube and twitter feature

    def _rss_parser(self) -> None:
        path = rss_file()
        articles: list[RssData] = []
        for url in RSS_FEEDS:
            feed = feedparser.parse(url)
            if "status" in feed and feed.status == 200:
                for entry in feed.entries:
                    article = RssData.from_entry(entry, feed.channel.title)
                    articles.append(article)
        articles.sort(key=lambda x: x.pub_date)
        with open(path, "w") as outfile:
            articles_dict_list = [article.__dict__ for article in articles]
            dump(articles_dict_list, outfile)

    def _read_rss(self) -> list[RssData]:
        path = rss_file()
        with open(path, "r") as infile:
            return [RssData(**article) for article in load(infile)]


class LoadFeeds:
    def _load_feeds(self) -> list[RssData]:
        RssCollection()._rss_parser()
        date_formats = ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"]
        all_feeds = RssCollection()._read_rss()

        sorted_feeds = sorted(
            all_feeds,
            key=lambda sort: self.parse_pub_date(sort.pub_date, date_formats),
        )

        return sorted_feeds

    def parse_pub_date(self, pub_date, date_formats):
        for date_format in date_formats:
            try:
                return datetime.strptime(pub_date, date_format)
            except ValueError:
                pass


if __name__ == "__main__":
    print(RSS_FEEDS)
