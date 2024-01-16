import argparse
from data.config import add_link, remove_link
from app import RssCli


def main():
    parser = argparse.ArgumentParser(description="Simple RSS reader from Terminal.")
    parser.add_argument("-a", "--add", type=str, help="Add an RSS link")
    parser.add_argument("-r", "--remove", type=str, help="Remove an RSS link")
    args = parser.parse_args()

    if args.add:
        add_link(args.add)
    elif args.remove:
        remove_link(args.remove)
    else:
        RssCli().main()


if __name__ == "__main__":
    main()
