# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Bluesky feed generator that creates a custom feed for smart home and home automation content. It's part of the **Smart Home Newsletter** (https://smarthomenewsletter.com) ecosystem.

**Business Goal:** Provide value to the smart home community on Bluesky while drawing potential subscribers to the Smart Home Newsletter. The feed should surface high-quality, relevant smart home content that demonstrates the newsletter's expertise and value.

This is a **static feed generator** that runs as a scheduled GitHub Action, searches Bluesky for relevant posts, and deploys pre-generated JSON files to Cloudflare Pages.

## Development Setup

**Package Manager:** This project uses `uv` (not pip/poetry/pipenv)

Install dependencies:
```bash
uv sync
```

Run scripts:
```bash
uv run python scripts/update_feed.py
uv run python scripts/publish_feed.py
```

Linting:
```bash
uv run ruff check .
uv run ruff format .
```

## Architecture

### Static Feed Generation Flow

1. **Search** ([src/search.py](src/search.py)) - Searches Bluesky's public API for posts matching keywords from `SEARCH_KEYWORDS` in [src/config.py](src/config.py)
2. **Algorithm** ([src/algorithm.py](src/algorithm.py)) - Filters and ranks posts by date (newest first)
3. **Generator** ([src/generator.py](src/generator.py)) - Writes static JSON files to `output/` directory:
   - `output/.well-known/did.json` - DID document identifying the feed generator
   - `output/xrpc/app.bsky.feed.getFeedSkeleton` - Feed skeleton with post URIs
   - `output/_headers` - Cloudflare Pages headers config

### Key Design Decisions

**No Backend Server:** This is not a traditional feed generator with a web server. It pre-generates static JSON files that Cloudflare Pages serves directly. Bluesky clients fetch these static files.

**Authentication:** The feed itself is unauthenticated and uses Bluesky's public API. Authentication is only needed for `publish_feed.py` (one-time feed registration) via `BSKY_HANDLE` and `BSKY_PASSWORD` environment variables.

**Deployment:** GitHub Actions runs `update_feed.py` every 30 minutes, then deploys the `output/` directory to Cloudflare Pages using the Wrangler action.

## Configuration

All feed configuration is in [src/config.py](src/config.py):
- `FEED_URI` / `FEED_DID` / `FEED_HOSTNAME` - Feed identity (must match domain)
- `SEARCH_KEYWORDS` - List of hashtags and phrases to search for
- `FEED_SIZE` - Number of posts to include in feed (default 50)
- `LANGUAGE` - Language filter for search (default "en")

## Scripts

- [scripts/update_feed.py](scripts/update_feed.py) - Main script run by GitHub Actions to update the feed
- [scripts/publish_feed.py](scripts/publish_feed.py) - One-time script to register feed on Bluesky (requires authentication)

## Python Version

Requires Python 3.14+ (see [pyproject.toml](pyproject.toml))
