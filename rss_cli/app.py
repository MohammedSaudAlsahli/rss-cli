from .models import RssData, LoadFeeds
from .widgets import RssTable, UserInput, Article, BaseClass


# todo: refactor this
class RssCli(BaseClass):
    def __init__(self) -> None:
        self._load = LoadFeeds()._load_feeds()

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


if __name__ == "__main__":
    RssCli().main()
