from .base_class import BaseClass
from ..models import RssData


class UserInput(BaseClass):
    def _user_input(self, load: list[RssData]):
        while True:
            user_input = self._prompt.ask(
                '\nenter the [b]ID[/] of feed or "[b][red]Q[/]" to quit'
            )
            if user_input.lower() == "q":
                return "q"
            try:
                user_input_int = int(user_input)
                if 1 <= user_input_int <= len(load):
                    return user_input
                else:
                    self._console.print(
                        "\n[b][red]Invalid feed [b]ID[/b]. Please enter a valid ID[/]"
                    )
            except ValueError:
                self._console.print(
                    '[b][red]Invalid input. Please enter a valid feed [b]ID[/b] or  "Q" to quit[/]'
                )
