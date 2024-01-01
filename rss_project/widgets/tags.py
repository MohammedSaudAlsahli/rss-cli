from __future__ import annotations

from typing_extensions import Final, Self

from textual import on
from textual.binding import Binding
from textual.events import Focus
from textual.reactive import var
from textual.widgets.option_list import Option, OptionDoesNotExist

from rich.console import RenderableType
from rich.emoji import Emoji
from rich.table import Table

from rss_project.messages.tags import ShowAlsoTaggedWith, ShowTaggedWith, ClearTags
from rss_project.widgets.extended_option_list import OptionListEx


class Tags(OptionListEx):
    DEFAULT_CSS = """
    Tags, Tags.focus {
        border: blank;
    }
    
    Tags > .option-list--option {
        padding: 0 1; 
    }
    """

    BINDINGS = [
        Binding("enter", "select", "Show tagged", show=True),
        Binding("+", "also_tagged", "Show also tagged"),
    ]

    def _prompt(self, tag: str, count: int) -> RenderableType:
        prompt = Table.grid(expand=True)
        prompt.add_column(ratio=1)
        prompt.add_column(justify="right")
        prompt.add_row(tag, f"[dim i]{count}[/]")
        return prompt

    def _sorted(self, tags: list[tuple[str, int]]) -> list[tuple[str, int]]:
        return tags

    def show(self, tags: list[tuple[str, int]]) -> Self:
        self.can_focus = bool(tags)
        highlighted_tag = (
            self.get_option_at_index(self.highlighted).id
            if self.highlighted is not None
            else None
        )
        try:
            return self.clear_options(
                [
                    Option(self._prompt(tag, count), id=tag)
                    for tag, count in self._sorted(tags)
                ]
            )
        finally:
            if tags:
                try:
                    self.highlighted = self.get_option_index(highlighted_tag or "")
                except OptionDoesNotExist:
                    self.highlighted = 0

    def _on_focus(self, _: Focus) -> None:
        if self.option_count and self.highlighted is None:
            self.highlighted = 0

    @on(OptionListEx.OptionSelected)
    def _show_tagged(self, event: OptionListEx.OptionSelected) -> None:
        """Request that bookmarks of a given tag are shown.

        Args:
            event: The event to handle.
        """
        if event.option.id is not None:
            self.post_message(ShowTaggedWith(event.option.id))

    def action_also_tagged(self) -> None:
        """Request that the current tag is added to any tag filter in place."""
        if self.highlighted is not None:
            if (tag := self.get_option_at_index(self.highlighted).id) is not None:
                self.post_message(ShowAlsoTaggedWith(tag))


class TagsMenu(Tags):
    BINDINGS = [Binding("c", "clear", "Clear Tags")]
    sort_by_count: var[bool] = var(False)

    def _sorted(self, tags: list[tuple[str, int]]) -> list[tuple[str, int]]:
        return (
            sorted(tags, key=lambda tag: tag[1], reverse=True)
            if self.sort_by_count
            else tags
        )

    def action_clear(self) -> None:
        self.post_message(ClearTags())


class InlineTags(Tags):
    DEFAULT_CSS = """
    InlineTags > .option-list--option {
        padding: 0;
    }
    """
    _ICON: Final[str] = Emoji.replace(":bookmark: ")

    def _prompt(self, tag: str, count: int) -> RenderableType:
        del count
        return f"{self._ICON} {tag}"
