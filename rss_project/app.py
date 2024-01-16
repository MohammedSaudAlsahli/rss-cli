from rich.table import Table
from rich.console import Console
from rss_project.models.rss_model import RssCollection, RssData
from rich.prompt import Prompt
from webbrowser import open as open_url
from rich.panel import Panel
from rich import box


class RssCli:
    def __init__(self) -> None:
        self._load = self._load_feeds()

    def main(self):
        while True:
            Console().print(self._feed_table())
            user_input = self._user_input()

            match user_input.lower():
                case "q":
                    exit()
                case _:
                    self.handle_articles(user_input, self._load)

    def _feed_table(self):
        table = Table(
            show_lines=True,
            box=box.ROUNDED,
            highlight=True,
            expand=False,
        )
        table.add_column(
            "id",
            justify="center",
            style="grey78",
        )
        table.add_column(
            "title",
            justify="center",
            style="grey78",
        )
        table.add_column(
            "provider",
            justify="center",
            style="grey78",
        )
        table.add_column(
            "published at",
            justify="center",
            style="grey78",
        )
        for index, article in enumerate(self._load):
            table.add_row(
                str(index + 1),
                article.title,
                article.provider,
                article.pub_date,
            )
        return table

    def _user_input(self):
        while True:
            user_input = Prompt.ask('\nenter the id of feed or "[b][red]q[/]" to quit')
            if user_input.lower() == "q":
                return "q"

            try:
                user_input_int = int(user_input)
                if 1 <= user_input_int <= len(self._load):
                    return user_input
                else:
                    Console().print(
                        "\n[b][red]Invalid feed ID. Please enter a valid ID.[/]"
                    )

            except ValueError:
                Console().print(
                    '[b][red]Invalid input. Please enter a valid feed ID or "[b][red]q[/]" to quit.[/]'
                )

    def clean_view(self, selected_article: RssData):
        clean_view_panel = Panel(
            f"\n{selected_article.description}\n"
            f"\n[b]By:[/] {selected_article.author}\n"
            f"\n[b]Visit:[/] {selected_article.link}",
            title=f"[b][dim]{selected_article.title}[/]",
            subtitle=f"[dim]{selected_article.provider}[/] at [dim]{selected_article.pub_date}[/]",
            subtitle_align="left",
            style="white",
            padding=1,
        )
        Console().print(clean_view_panel, justify="center")
        while True:
            user_input = Prompt.ask(
                '\nPress "v" to visit the article or "[b][red]e[/]" to return to the main view.'
            )
            match user_input.lower():
                case "e":
                    return
                case "v":
                    open_url(selected_article.link)
                    return
                case _:
                    Console().print(
                        '[b][red]Invalid input. Please press "v" to visit the article or "[b][red]e[/]" to exit.[/]'
                    )

    def handle_articles(self, selected_id, data):
        selected_id = int(selected_id)
        selected_article: RssData = data[selected_id - 1]
        self.clean_view(selected_article)

    def _load_feeds(self) -> list[RssData]:
        RssCollection()._rss_parser()
        all_feeds = RssCollection()._read_rss()
        return all_feeds


if __name__ == "__main__":
    Console().print(RssCli().main())
