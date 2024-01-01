
from pathlib import Path

from .locations import data_dir


def rss_file() -> Path:
    """The path to the file that the local rss are held in.

    Returns:
        The path to the rss file.
    """
    return data_dir() / "rss.json"



