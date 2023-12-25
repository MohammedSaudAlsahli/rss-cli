import argparse
import re
from rss_cli.view.tui import RssCli
from rss_cli.utils.default_config import FEEDS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--append", type=str, help="Add RSS link")
    args = parser.parse_args()

    if args.append:
        FEEDS.append(args.append)
        print("Added rss link:", args.append)
    else:
        RssCli().run()
