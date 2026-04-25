# RSS CLI

A beautiful terminal RSS feed reader powered by [Textual](https://textual.textualize.io/).

![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![PyPI](https://img.shields.io/pypi/v/rss-cli)

## Features

- **Interactive TUI** — Full terminal UI with keyboard navigation, not just text output
- **Source-type Tabs** — Filter articles by source: All, RSS, Reddit, Twitter/X, Bookmarks
- **RSS Marketplace** — Discover and subscribe to feeds by category or search (powered by Feedly)
- **Full Article Fetch** — Press `f` to fetch the full article content from the web when RSS feeds only provide snippets
- **HTML → Markdown** — Rich article rendering with proper headings, links, lists, code blocks, and more
- **Article Pagination** — Browse 25 articles at a time with "Load more" for large feeds
- **Article Numbering** — See your position: `1/62` shows article index and total count
- **Read Tracking** — Articles are marked as read automatically
- **Bookmarks** — Save articles with `b` and view them in the Bookmarks tab
- **Search** — Filter articles by keyword across title, description, author, and feed
- **Feed Management** — Add, remove, and browse RSS feeds interactively
- **Reddit & Twitter/X** — Built-in support for Reddit RSS and Nitter (Twitter/X) feeds with instance fallback
- **Caching** — Feeds are cached with configurable TTL (30 min default)
- **Parallel Fetching** — All feeds fetched concurrently with async httpx
- **Browser Integration** — Open articles in your default browser with `o`
- **Theme Cycling** — Switch between dark themes with `t`
- **Refresh Notifications** — See "Refreshing feeds…" and "✓ Refreshed X feeds · Y articles"

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

| Key | Action |
|-----|--------|
| `Enter` | Read selected article |
| `f` | Fetch full article from the web |
| `o` | Open article in browser |
| `b` | Toggle bookmark |
| `n` / `p` | Next / previous article (in reader) |
| `a` | Add new feed |
| `m` | Open RSS marketplace |
| `d` | Delete a feed |
| `s` | Search articles |
| `r` | Refresh feeds |
| `t` | Cycle theme |
| `Esc` | Go back |
| `q` | Quit |
| `?` | Help |

### CLI Commands

```bash
rss add <url>       # Add a feed
rss remove <url>    # Remove a feed
rss list            # List all feeds
rss refresh         # Fetch all feeds
rss read            # Launch the TUI
rss --version       # Show version
```

### Source Tabs

The left panel has tabs to filter articles by source type:

- **All** — Every article from all feeds
- **RSS** — Standard RSS/Atom feeds
- **Reddit** — Reddit subreddit feeds (auto-detected from URL)
- **Twitter** — Nitter/Twitter feeds (auto-detected from URL)
- **Bookmarks** — Your saved articles

### RSS Marketplace

Press `m` to open the marketplace where you can:

- Browse curated categories (Tech, Programming, AI, Science, etc.)
- Search for feeds by keyword
- See subscriber counts for each feed
- Press `Enter` to subscribe instantly

### Full Article Fetch

When an RSS feed only provides a short snippet, press `f` in the article reader to:

1. Fetch the full web page
2. Extract the main article content using readability-lxml
3. Convert HTML to Markdown for beautiful terminal rendering
4. Cache the result for the session

## Configuration

Config and data are stored in XDG-compliant directories:

- **Config**: `~/.config/rss-cli/`
- **Cache**: `~/.cache/rss-cli/`
- **Data**: `~/.local/share/rss-cli/`

### Custom Settings

Create `~/.config/rss-cli/config.toml`:

```toml
[settings]
cache_ttl_seconds = 1800       # Cache duration (default: 30 min)
max_articles_per_feed = 200    # Max articles per feed

[twitter]
nitter_instances = [
    "nitter.net",
    "xcancel.com",
    "nitter.poast.org",
    "nitter.privacyredirect.com",
]
```

### Adding Feeds

**RSS feeds:**
```bash
rss add https://news.ycombinator.com/rss
```

**Reddit subreddits** (auto-detected):
```bash
rss add https://www.reddit.com/r/python/.rss
```

**Twitter/X via Nitter** (auto-detected):
```bash
rss add https://nitter.net/elonmusk/rss
```

## Recommended RSS Feeds

- [Hacker News](https://news.ycombinator.com/rss) — Tech news
- [BBC News](http://feeds.bbci.co.uk/news/rss.xml) — World news
- [TechCrunch](https://techcrunch.com/feed/) — Tech startup news
- [The Verge](https://www.theverge.com/rss/index.xml) — Technology and culture
- [r/Python](https://www.reddit.com/r/python/.rss) — Python community
- [r/Programming](https://www.reddit.com/r/programming/.rss) — Programming discussion

Find more in the built-in marketplace (press `m`) or at [rss.com/blog/popular-rss-feeds](https://rss.com/blog/popular-rss-feeds/).

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

## Changelog

### v0.3.0

- **Source-type tabs** — Filter articles by All, RSS, Reddit, Twitter, Bookmarks
- **RSS Marketplace** — Discover and subscribe to feeds by category or search
- **Full article fetch** — Press `f` to fetch full article content from the web
- **HTML → Markdown** — Rich rendering with headings, links, lists, code blocks
- **Article pagination** — Browse 25 articles at a time with "Load more"
- **Article numbering** — See position like `1/62` in the article list
- **Refresh notifications** — "Refreshing feeds…" → "✓ Refreshed X feeds · Y articles"
- **DateTime fix** — All datetimes are UTC-aware, preventing comparison errors
- **max_articles_per_feed** raised from 50 to 200

### v0.2.0

- Reddit and Twitter/X feed support with Nitter fallback
- Async feed fetching with httpx
- OOP refactor — CSS, themes, utils, dialogs extracted

### v0.1.0

- Initial release

## License

MIT © Mohammed Alsahli