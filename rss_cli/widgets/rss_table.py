from rich import box
from rich.table import Table

from .base_class import BaseClass
from ..models import RssData


class RssTable(BaseClass):
    def feeds_table(self, load: list[RssData]):
        table = Table(
            show_lines=True,
            box=box.SQUARE,
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
        if not load:
            self._console.print("[i]No data yet...[/i]")
            exit()

        for index, article in enumerate(load):
            table.add_row(
                str(index + 1),
                article.title,
                article.provider,
                article.pub_date,
            )
        return table
