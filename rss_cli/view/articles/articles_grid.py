from typing import Any, Coroutine
from textual.events import Key
from textual.widget import Widget
from rss_cli.articles.feeds import get_content
from textual.containers import Grid
from rss_cli.view.articles.article_card import ArticleCard
from textual.app import ComposeResult
from textual import events
from rss_cli.view.articles.full_article import FullArticle


# class ArticlesGrid(Grid):
#     def compose(self) -> ComposeResult:
#         feeds = get_content()
#         for provider, feed in feeds.items():
#             for articles in feed:
#                 article = ArticleCard(f"{articles.title}")
#                 article.border_title = provider
#                 article.border_subtitle = articles.pub_date
#                 yield article

#     # def handle_key(self):
#     #     ...


#     def content(self) -> None:
#         ...


class ArticlesGrid(Grid):
    def compose(self) -> ComposeResult:
        for article_info in self.content:
            article = ArticleCard(article_info.get("title"))
            article.border_title = article_info.get("provider")
            article.border_subtitle = article_info.get("pub_date")
            yield article

    # def handle_key(self, event: events.Key) -> bool:
    #     if event.key == "enter":
    #         focused_card = self.focus()
    #         if focused_card is not None:
    #             self.app.push_screen(...)

    @property
    def content(self):
        feeds = get_content()
        data = []
        for provider, feed in feeds.items():
            for article in feed:
                data.append(
                    {
                        "provider": provider,
                        "title": article.title,
                        "description": article.description,
                        "content": article.content,
                        "link": article.link,
                        "pub_date": article.pub_date,
                        "author": article.author,
                        "authors": article.authors,
                        "tags": article.tags,
                    }
                )
        return data
