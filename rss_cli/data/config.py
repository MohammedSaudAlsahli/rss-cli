from pathlib import Path
import os


def add_link(link):
    rss_list_path = rss_list()

    if link not in open(rss_list_path).read():
        with open(rss_list_path, "a") as list_file:
            list_file.write(f"{link}\n")
        print(f"Link '{link}' added successfully.")
    else:
        print(f"Link '{link}' already exists in the list.")


def remove_link(link):
    rss_list_path = rss_list()
    with open(rss_list_path, "r") as list_file:
        existing_links = [line.strip() for line in list_file.readlines()]
    print(f"Existing Links Before Removal: {existing_links}")
    if link in existing_links:
        existing_links.remove(link)
        print(f"Existing Links After Removal: {existing_links}")
        with open(rss_list_path, "w") as list_file:
            list_file.write("\n".join(existing_links))
            list_file.write("\n")
        print(f"Link '{link}' removed successfully.")
    else:
        print(f"Link '{link}' not found in the list.")


def read_list_file():
    rss_list_path = rss_list()
    with open(rss_list_path, "r") as list_file:
        lines = list_file.readlines()
        return [line.strip() for line in lines]


def rss_list() -> Path:
    file_path = Path(os.getcwd()) / "rss_list.txt"
    if not file_path.exists():
        file_path.touch()

    return file_path


def rss_file() -> Path:
    return Path(os.getcwd()) / "rss.json"


RSS_FEEDS = [rss_link for rss_link in read_list_file()]

if __name__ == "__main__":
    dir_path = os.getcwd()
    print(dir_path)
