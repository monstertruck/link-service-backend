# Plan: Fetch Page Summary Function

## Goal
Add a utility function that takes a URL, fetches the page content using the appropriate browser driver, and returns a brief summary of the main body text (first N words).

## Placement
`lib/utils.py` — the natural home for shared utility logic in this project.

## Approach

### Dual-driver strategy
1. **httpx (fast path)** — attempt a lightweight async HTTP GET first. No browser overhead, works for the majority of static pages.
2. **Playwright/Chromium (fallback)** — if the extracted text is below a minimum word threshold (`_JS_RENDER_THRESHOLD = 50`), the page is assumed to be JS-rendered and Playwright launches a headless Chromium browser to render it fully before extracting text.

### Text extraction
- Strip noise tags: `script`, `style`, `nav`, `header`, `footer`, `aside`, `noscript`
- Prefer semantic content containers: `<main>` → `<article>` → `<body>` → full document
- Collapse whitespace; return first `word_limit` words (default: 200)

## Functions Added (`lib/utils.py`)
| Function | Visibility | Purpose |
|---|---|---|
| `fetch_page_summary(url, word_limit)` | public | Entry point; returns summary string |
| `_fetch_html(url)` | private | Tries httpx, falls back to Playwright |
| `_needs_js(html)` | private | Heuristic: too-little text → JS page |
| `_playwright_fetch(url)` | private | Headless Chromium render via Playwright |
| `_extract_body_text(html)` | private | BeautifulSoup extraction + cleanup |

## Dependencies Added
- `httpx>=0.27` — async HTTP client
- `beautifulsoup4>=4.12` — HTML parsing
- `lxml>=5.0` — fast BS4 parser backend
- `playwright>=1.44` — headless browser automation

Added to both `pyproject.toml` and `requirements.in`. Installed via `uv sync`. Playwright Chromium binary installed via `playwright install chromium`.

## Future Considerations
- Could integrate `fetch_page_summary` into an API endpoint (e.g. POST `/links` auto-populates `summary` field on the `Link` schema).
- Word limit could be made a configurable app setting rather than a per-call parameter.
- Could add a `readability`-style library (e.g. `trafilatura`) as a more robust content extractor if BS4 proves noisy on complex pages.
