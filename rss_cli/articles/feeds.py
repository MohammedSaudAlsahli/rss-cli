from rss_cli.utils.default_config import FEEDS
import feedparser
from rss_cli.articles.models.rss_model import RssModel


# create class to see if the url is rss feed or html omly to make function cleaner, for youtube and twitter
# class -> function see if it rss -> if rss -> rss function, else -> html function


def get_content() -> dict[str, list[dict]]:
    """Get content from url
    Args:
        urls: urls: List of URL strings.
    Returns:
        A dictionary with provider names as keys and a list of articles as values.
    """

    articles: dict[str, list[RssModel]] = {}

    for url in FEEDS:
        feed = feedparser.parse(url)
        if feed.status == 200:
            provider = feed.channel.title

            for entry in feed.entries:
                if provider not in articles:
                    articles[provider] = []

                article = RssModel.from_entry(entry)
                articles[provider].append(article)

    return articles


def convert_to_rss(url: str):
    ...
