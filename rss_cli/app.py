from datetime import datetime

from .models import RssCollection, RssData
from .widgets import RssTable, UserInput, Article, BaseClass


# todo: refactor this
class RssCli(BaseClass):
    def __init__(self) -> None:
        self._load = self._load_feeds()

    def main(self):
        while True:
            self._console.print(RssTable().feeds_table(self._load))
            user_input = UserInput()._user_input(self._load)

            match user_input.lower():
                case "q":
                    exit()
                case _:
                    self._handle_articles(user_input, self._load)

    def _handle_articles(self, selected_id, data):
        selected_id = int(selected_id)
        selected_article: RssData = data[selected_id - 1]
        Article()._view(selected_article)

    def _load_feeds(self) -> list[RssData]:
        RssCollection()._rss_parser()
        all_feeds = RssCollection()._read_rss()

        sorted_feeds = sorted(
            all_feeds,
            key=lambda sort: datetime.strptime(
                sort.pub_date, "%a, %d %b %Y %H:%M:%S %z"
            ),
        )

        return sorted_feeds


if __name__ == "__main__":
    RssCli().main()
