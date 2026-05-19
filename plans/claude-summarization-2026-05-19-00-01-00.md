# Plan: Claude-Based Summarization

## Goal
Replace the naive word-truncation summary in `lib/utils.py` with genuine LLM summarization via the Anthropic Claude API.

## File Changes

### New: `lib/llm.py`
All LLM interaction lives here.

| Function | Purpose |
|---|---|
| `summarize_text(text)` | Sends extracted page text to Claude and returns a concise summary string |
| `summarize_url(url)` | Convenience wrapper: fetches page text via `lib/utils.py`, then calls `summarize_text` |

- Claude model: `claude-3-5-haiku-latest` (fast, cheap, good for summarization)
- API key read from environment variable `ANTHROPIC_API_KEY` via `os.environ`; raises a clear `RuntimeError` at call time if missing (never hard-coded)
- Input text is truncated to a safe token budget (~4000 words) before sending to avoid exceeding context limits

### Modified: `lib/utils.py`
- `fetch_page_summary` renamed → `fetch_page_text` (returns full extracted body text, not a word-truncated slice)
- The word-limit parameter is removed; callers that want raw truncation can slice themselves
- All page-fetching private helpers remain unchanged

## Dependencies Added
- `anthropic>=0.28` — official Anthropic Python SDK

Added to `pyproject.toml` and `requirements.in`, installed via `uv sync`.

## Security
- API key is never logged, committed, or interpolated into strings
- Loaded once at call time via `os.environ.get("ANTHROPIC_API_KEY")`; a missing key raises `RuntimeError` with a helpful message
