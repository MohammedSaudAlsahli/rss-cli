"""CLI commands — Typer-based entry point."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from rss_cli import __version__

app = typer.Typer(
    name="rss-cli",
    help="A beautiful terminal RSS feed reader.",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"rss-cli v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool | None = typer.Option(
        None, "--version", "-v", help="Show version.", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Launch the TUI app if no subcommand is given."""
    if ctx.invoked_subcommand is not None:
        return
    _launch_tui()


@app.command()
def read() -> None:
    """Launch the interactive TUI reader."""
    _launch_tui()


@app.command()
def add(url: str = typer.Argument(..., help="RSS feed URL to add")) -> None:
    """Add a new RSS feed subscription."""
    from rss_cli.services.config import save_feed_url

    if save_feed_url(url):
        console.print(f"[green]✓ Added:[/green] {url}")
    else:
        console.print(f"[yellow]Already exists:[/yellow] {url}")


@app.command(name="add-reddit")
def add_reddit(
    subreddit: str = typer.Argument(
        ..., help="Subreddit name (e.g. 'python' or 'r/python')"
    ),
) -> None:
    """Add a Reddit subreddit feed."""
    from rss_cli.services.config import build_reddit_url, save_feed_url

    url = build_reddit_url(subreddit)
    if save_feed_url(url):
        console.print(f"[green]✓ Added:[/green] {url}")
    else:
        console.print(f"[yellow]Already exists:[/yellow] {url}")


@app.command(name="add-twitter")
def add_twitter(
    username: str = typer.Argument(
        ..., help="Twitter username (e.g. 'elonmusk' or '@elonmusk')"
    ),
) -> None:
    """Add a Twitter/X account feed via Nitter."""
    from rss_cli.services.config import build_nitter_url, save_feed_url

    url = build_nitter_url(username)
    if save_feed_url(url):
        console.print(f"[green]✓ Added:[/green] {url}")
    else:
        console.print(f"[yellow]Already exists:[/yellow] {url}")


@app.command()
def remove(url: str = typer.Argument(..., help="RSS feed URL to remove")) -> None:
    """Remove an RSS feed subscription."""
    from rss_cli.services.config import remove_feed_url

    if remove_feed_url(url):
        console.print(f"[green]✓ Removed:[/green] {url}")
    else:
        console.print(f"[red]Not found:[/red] {url}")


@app.command(name="list")
def list_feeds() -> None:
    """List all subscribed feeds."""
    from rss_cli.services.config import load_feed_urls

    urls = load_feed_urls()
    if not urls:
        console.print("[dim]No feeds subscribed yet.[/dim]")
        console.print("Add one with: [bold]rss add <url>[/bold]")
        return

    table = Table(title="RSS Feeds", show_lines=True)
    table.add_column("#", style="dim")
    table.add_column("URL")

    for i, url in enumerate(urls, 1):
        table.add_row(str(i), url)

    console.print(table)


@app.command()
def refresh() -> None:
    """Fetch and cache all feeds."""
    from rss_cli.services.fetcher import fetch_feeds_sync

    with console.status("[bold green]Fetching feeds..."):
        feeds = fetch_feeds_sync()

    console.print(f"[green]✓ Refreshed {len(feeds)} feeds[/green]")
    for feed in feeds:
        console.print(f"  {feed.title}: {feed.article_count} articles")


@app.command()
def bookmarks() -> None:
    """List bookmarked articles."""
    from rss_cli.services.cache import apply_all_state, load_bookmarks, load_cache

    articles = load_cache()
    if articles is None:
        console.print("[dim]No cached articles. Run [bold]rss refresh[/bold] first.[/dim]")
        return

    articles = apply_all_state(articles)
    bookmarked_links = load_bookmarks()

    if not bookmarked_links:
        console.print("[dim]No bookmarks yet.[/dim]")
        console.print("Use [bold]b[/bold] in the TUI to bookmark articles.")
        return

    bookmarked = [a for a in articles if a.link in bookmarked_links]
    if not bookmarked:
        console.print("[dim]No bookmarked articles found.[/dim]")
        return

    table = Table(title="Bookmarked Articles", show_lines=True)
    table.add_column("#", style="dim")
    table.add_column("Title")
    table.add_column("Feed")
    table.add_column("Date")

    for i, a in enumerate(bookmarked, 1):
        table.add_row(str(i), a.title, a.feed_title, a.pub_date_display)

    console.print(table)


def _launch_tui() -> None:
    """Launch the Textual TUI application."""
    from rss_cli.app import RssCliApp

    rss_app = RssCliApp()
    rss_app.run()


if __name__ == "__main__":
    app()
