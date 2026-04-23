# RSS CLI

A beautiful terminal RSS feed reader powered by [Textual](https://textual.textualize.io/).

![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Interactive TUI** — Full terminal UI with keyboard navigation, not just text output
- **Feed Management** — Add, remove, and browse RSS feeds interactively
- **Article Reader** — Read article content directly in the terminal
- **Search** — Filter articles by keyword
- **Read Tracking** — Articles are marked as read automatically
- **Caching** — Feeds are cached with configurable TTL (5 min default)
- **Parallel Fetching** — All feeds fetched concurrently for speed
- **Browser Integration** — Open articles in your default browser

## Install

```bash
pip install rss-cli
```

Or install from source:

```bash
git clone https://github.com/MohammedSaudAlsahli/rss-cli.git
cd rss-cli
uv sync
```

## Usage

### Interactive TUI (recommended)

```bash
rss
```

This launches the full terminal UI where you can:
- Press `a` to add a feed
- Press `Enter` to open a feed and browse articles
- Press `s` to search articles
- Press `o` to open an article in your browser
- Press `?` for help
- Press `q` to quit

### CLI Commands

```bash
rss add <url>       # Add a feed
rss remove <url>    # Remove a feed
rss list            # List all feeds
rss refresh         # Fetch all feeds
rss read            # Launch the TUI
rss --version       # Show version
```

### Key Bindings

| Key | Action |
|-----|--------|
| `a` | Add new feed |
| `d` | Delete selected feed |
| `r` | Refresh feeds |
| `Enter` | Open selected item |
| `o` | Open in browser |
| `s` | Search articles |
| `Esc` | Go back |
| `q` | Quit |
| `?` | Help |

## Configuration

Config and data are stored in XDG-compliant directories:

- **Config**: `~/.config/rss-cli/`
- **Cache**: `~/.cache/rss-cli/`
- **Data**: `~/.local/share/rss-cli/`

### Custom Settings

Create `~/.config/rss-cli/config.toml`:

```toml
[settings]
cache_ttl_seconds = 300        # Cache duration (default: 5 min)
max_articles_per_feed = 50     # Max articles per feed
```

## Recommended RSS Feeds

- [Hacker News](https://news.ycombinator.com/rss) — Tech news
- [BBC News](http://feeds.bbci.co.uk/news/rss.xml) — World news
- [TechCrunch](https://techcrunch.com/feed/) — Tech startup news
- [The Verge](https://www.theverge.com/rss/index.xml) — Technology and culture

Find more at [rss.com/blog/popular-rss-feeds](https://rss.com/blog/popular-rss-feeds/).

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Type check
uv run mypy rss_cli

# Run the app
uv run rss
```

## License

MIT © Mohammed Alsahli
