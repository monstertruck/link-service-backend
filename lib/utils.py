"""Utils for handling links."""

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _load_config() -> dict:
    try:
        return yaml.safe_load(_CONFIG_PATH.read_text()) or {}
    except Exception:
        return {}


def _netloc(url: str) -> str:
    return urlparse(url).netloc.lower().lstrip("www.")


def is_skipped_domain(url: str) -> bool:
    """Return True if *url*'s hostname is in the skip_domains config list."""
    skip_domains = _load_config().get("skip_domains") or []
    netloc = _netloc(url)
    return any(netloc == d.lower().lstrip("www.") for d in skip_domains)


def is_podcast_url(url: str) -> bool:
    """Return True if *url*'s hostname is in the podcast_domains config list."""
    podcast_domains = _load_config().get("podcast_domains") or []
    netloc = _netloc(url)
    return any(netloc == d.lower().lstrip("www.") for d in podcast_domains)

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Tags that don't contribute to readable body content
_NOISE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "noscript"]

# Minimum word count from a plain HTTP fetch before we consider the page
# JS-rendered and fall back to Playwright.
_JS_RENDER_THRESHOLD = 50


async def fetch_page_title_and_text(url: str) -> tuple[str | None, str]:
    """Return (title, body_text) for *url* in a single fetch."""
    html = await _fetch_html(url)
    title = _extract_title(html)
    text = _extract_body_text(html)
    return title, text


async def fetch_page_text(url: str) -> str:
    """Fetch *url* and return the clean body text.

    Strategy:
    - Attempt a lightweight HTTP GET via httpx.
    - If the extracted text has fewer than _JS_RENDER_THRESHOLD words the page
      likely requires JavaScript to render; Playwright is used as a fallback.
    - Main body text is extracted by preferring <main> / <article> elements and
      stripping navigation, headers, footers, and script/style noise.
    """
    html = await _fetch_html(url)
    return _extract_body_text(html)


async def _fetch_html(url: str) -> str:
    """Return the HTML for *url*, using Playwright when the page needs JS."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (compatible; link-service-bot/1.0)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError:
        html = ""

    if _needs_js(html):
        html = await _playwright_fetch(url)

    return html


def _needs_js(html: str) -> bool:
    """Return True when the page has too little readable text to be useful."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(_NOISE_TAGS):
        tag.decompose()
    words = soup.get_text(separator=" ", strip=True).split()
    return len(words) < _JS_RENDER_THRESHOLD


async def _playwright_fetch(url: str) -> str:
    """Render *url* with a headless Chromium browser and return the full HTML."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30_000)
            html = await page.content()
        finally:
            await browser.close()
    return html


def is_youtube_url(url: str) -> bool:
    """Return True if *url* is a YouTube video or short link."""
    parsed = urlparse(url)
    return parsed.netloc in (
        "www.youtube.com", "youtube.com", "youtu.be", "m.youtube.com"
    )


def title_from_url(url: str) -> str:
    """Derive a human-readable title from a URL as a last resort.

    Examples:
        https://example.com/some-great-article  -> "Some Great Article"
        https://news.ycombinator.com            -> "news.ycombinator.com"
    """
    parsed = urlparse(url)
    # Use the last non-empty path segment, falling back to the hostname.
    segments = [s for s in parsed.path.split("/") if s]
    slug = segments[-1] if segments else ""
    # Strip common file extensions
    slug = re.sub(r'\.[a-z]{2,5}$', '', slug, flags=re.IGNORECASE)
    if slug:
        # Replace separators with spaces and title-case
        return re.sub(r'[-_]+', ' ', slug).title()
    return parsed.netloc or url


def _extract_title(html: str) -> str | None:
    """Return the text of the <title> tag, or None if absent."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("title")
    if tag and tag.string:
        return tag.string.strip() or None
    return None


def _extract_body_text(html: str) -> str:
    """Parse *html* and return clean body text with whitespace normalised."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # Prefer semantic content containers; fall back to <body> then whole doc.
    container = (
        soup.find("main")
        or soup.find("article")
        or soup.find("body")
        or soup
    )

    raw = container.get_text(separator=" ", strip=True)
    return " ".join(raw.split())

