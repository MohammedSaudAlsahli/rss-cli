from pathlib import Path
from rss_project.data.locations import data_dir


def rss_file() -> Path:
    return data_dir() / "rss.json"


if __name__ == "__main__":
    print(rss_file())
