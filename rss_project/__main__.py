import argparse

from .data.config import add_link, remove_link, RSS_FEEDS
from .app import RssCli


def main():
    parser = argparse.ArgumentParser(description="Simple RSS reader from Terminal.")
    parser.add_argument("-a", "--add", type=str, help="Add an RSS link")
    parser.add_argument("-r", "--remove", type=str, help="Remove an RSS link")
    parser.add_argument(
        "-l", "--list", type=str, nargs="?", const="list", help="View the feed list"
    )
    args = parser.parse_args()

    if args.add:
        add_link(args.add)
    elif args.remove:
        remove_link(args.remove)
    elif args.list:
        print(f"Feed List: {RSS_FEEDS}")

    else:
        RssCli().main()


if __name__ == "__main__":
    main()
