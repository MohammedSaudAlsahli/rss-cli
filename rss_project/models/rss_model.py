from dataclasses import dataclass
from uuid import uuid4
import feedparser
from json import dump, load

from rss_project.data.rss import rss_file


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
    tags: list[str]

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
            tags=[tag.term for tag in entry.get("tags", [])],
        )


class RssCollection:
    # Todo: if everything was right I will change this to a list of rss feeds that user add
    def _rss_feeds(self) -> list[str]:
        return [
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://podcastfeeds.nbcnews.com/RPWEjhKq",
            "https://feeds.megaphone.fm/newheights",
        ]

    # Todo: in the future I need to refactor this for youtube and twitter feature

    def _rss_parser(self) -> None:
        path = rss_file()
        articles: list[RssData] = []
        for url in self._rss_feeds():
            feed = feedparser.parse(url)
            if feed.status == 200:
                for entry in feed.entries:
                    article = RssData.from_entry(entry, feed.channel.title)
                    articles.append(article)
        with open(path, "w") as outfile:
            articles_dict_list = [article.__dict__ for article in articles]
            dump(articles_dict_list, outfile)

    def _read_rss(self) -> list[RssData]:
        path = rss_file()
        with open(path, "r") as infile:
            return [RssData(**article) for article in load(infile)]


if __name__ == "__main__":
    f = RssCollection()._rss_parser()
    print(f)
