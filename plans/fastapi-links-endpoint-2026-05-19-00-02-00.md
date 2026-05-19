# Plan: FastAPI Links Endpoint

## Goal
Add a POST `/links` endpoint that accepts a URL (and optional title/summary), auto-generates a summary via Claude if not provided, and assigns a category from `LinkCategory` based on that summary.

## Schema Changes (`app/api/schemas/links.py`)
- `Link.title` — change from `str` to `Optional[str] = None`
- `Link.category` — change type from `str` to `LinkCategory` for strict validation

Add two new models:
- `LinkRequest` — the request body (`url` required; `title`, `summary` optional)
- `LinkResponse` — the response body (same as `Link` but with guaranteed `summary` and `LinkCategory`)

## New Files

### `app/api/routes/links.py`
- `POST /links` — accepts `LinkRequest`, returns `LinkResponse`
  1. If `summary` not provided → call `summarize_url(url)` from `lib/llm.py`
  2. Call `categorize_link(summary)` from `lib/llm.py` to get a `LinkCategory`
  3. Return fully-populated `LinkResponse`

### `app/api/routes/__init__.py` — empty init

### `app/api/__init__.py` — empty init

### `app/__init__.py` — empty init

## LLM Changes (`lib/llm.py`)
Add `categorize_link(summary: str) -> LinkCategory`:
- Sends the summary to Claude with the list of valid categories
- Returns the matching `LinkCategory` enum value
- Falls back to `LinkCategory.OTHER` if Claude's response doesn't match any known value

## `main.py`
- Mount the links router at `/links`
- Keep existing root route

## No new dependencies needed — FastAPI and anthropic are already installed.
