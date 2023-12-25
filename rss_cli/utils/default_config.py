from rich.text import Text
import datetime


def get_clock() -> Text:
    return Text(f"{datetime.now().time().strftime(' %X ')}", "r " + Colors.cyan)


# Feeds
FEEDS: list[str] = [
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://feeds.megaphone.fm/newheights",
    # "https://podcastfeeds.nbcnews.com/RPWEjhKq",
    # "https://rss.art19.com/-exposed-",
]


# Colors
class Colors:
    dark_black = "#252a34"
    black = "#2e3440"
    white = "#e5e9f0"
    grey = "#d8dee9"
    red = "#bf616a"
    frost_green = "#8fbcbb"
    cyan = "#88c0d0"
    green = "#a3be8c"
    yellow = "#ebcb8b"
    blue = "#81a1c1"
    magenta = "#b48ead"
    orange = "#d08770"

    BACKGROUND = dark_black
    BAR_BACKGROUND = black
    BORDER_DIM = grey + " 50%"
    BORDER_LIT = blue
    BORDER_TITLE_DIM = grey, dark_black
    BORDER_TITLE_LIT = white, blue
    SEARCH_COLOR = red


RSS = {"new": "⬤", "read": "◯", "porinter": "→"}
EMPTY_RSS = ["No feeds yet", f"Press {('a', Colors.blue)} to add one"]

# keybindings
BINDINGS = [
    ("q", "request_quit"),
    ("d", "dark_mode"),
    # ("enter", "push_screen('test')", "test"),
    # ("a", "add_rss", "Add Rss"),
    # ("r", "refresh_rss", "Refresh Rss"),
    ("right", "focus_next", "Focus Next"),
    ("tab", "switch_screen", "Switch Screen"),  # make screens for providers and feeds
    ("left", "focus_previous", "Focus Previous"),
    ("escape", "pop_screen", "Pop screen"),
]
