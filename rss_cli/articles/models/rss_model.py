import re
from datetime import datetime


class RssModel:
    def __init__(
        self,
        title: str,
        description: str,
        content: list[str],
        link: str,
        pub_date: str,
        author: str,
        authors: list[str],
        tags: list[str],
    ) -> None:
        self.title = self.clean_text(title)
        self.description = self.clean_text(description)
        self.content = self.clean_text(content)
        self.link = self.clean_text(link)
        self.pub_date = self.readable_date(pub_date)
        self.author = self.clean_text(author)
        self.authors = self.clean_text(authors)
        self.tags = self.clean_text(tags)

    @classmethod
    def from_entry(cls, entry):
        return cls(
            title=entry.title,
            description=entry.description,
            content=[
                content.get("value", "no content")
                for content in entry.get("content", [])
            ],
            link=entry.links[0].get("href") if entry.links else None,
            pub_date=entry.published,
            author=entry.get("author"),
            authors=entry.get("author", []),
            tags=[tag.term for tag in entry.get("tags", [])],
        )

    def clean_text(self, value):
        cleaned_value = re.sub(r"<[^>]+>", "", str(value))
        return cleaned_value

    def readable_date(self, pub_date):
        date_format = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
        formated_pub_date = date_format.strftime("%a, %d %b %Y %I:%M:%S %p")
        return formated_pub_date
