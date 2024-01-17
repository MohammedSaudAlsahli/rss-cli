from webbrowser import open as open_url
from rich.panel import Panel

from .base_class import BaseClass
from ..models import RssData


class Article(BaseClass):
    def _view(self, selected_article: RssData):
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
        self._console.print(clean_view_panel, justify="center")
        while True:
            user_input = self._prompt.ask(
                '\nPress "[b][green]V[/]" to visit the article or "[b][green]E[/]" to return to the main view'
            )
            match user_input.lower():
                case "e":
                    return
                case "v":
                    open_url(selected_article.link)
                    return
                case _:
                    self._console.print(
                        '[b][red]Invalid input. Please press "[green]V[/green]" to visit the article or "[green]E[/green]" to exit[/]'
                    )
