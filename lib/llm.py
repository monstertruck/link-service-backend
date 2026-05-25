"""LLM utilities for summarizing and categorizing links via Claude."""

import logging
import os

import anthropic

logger = logging.getLogger(__name__)

from app.api.schemas.links import LinkCategory
from lib.utils import fetch_page_title_and_text  # noqa: E402

_ANTHROPIC_MODEL = "claude-haiku-4-5"

# Approximate word budget sent to the LLM.
_MAX_INPUT_WORDS = 500


def _get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")
    return anthropic.Anthropic(api_key=api_key)


def summarize_text(text: str) -> str:
    """Summarize *text* using Claude. Raises on failure."""
    truncated = " ".join(text.split()[:_MAX_INPUT_WORDS])
    client = _get_anthropic_client()
    message = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=128,
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarize the following web page content in 2-3 sentences. "
                    "Focus on what the page is about and its key points. "
                    "Reply with only the summary, no preamble.\n\n"
                    f"{truncated}"
                ),
            }
        ],
    )
    return message.content[0].text.strip()


async def summarize_url_with_title(url: str) -> tuple[str | None, str]:
    """Fetch *url* and return (html_title, summary) in a single page load."""
    logger.info("Fetching page url=%s", url)
    try:
        title, text = await fetch_page_title_and_text(url)
    except Exception as exc:
        logger.error("Failed to fetch page url=%s: %s", url, exc)
        raise
    logger.debug("Fetched page url=%s title=%r words=%d", url, title, len(text.split()))
    summary = summarize_text(text)
    logger.debug("Summary generated url=%s", url)
    return title, summary


def quick_summarize(hint: str) -> str:
    """Generate a one-sentence summary from a title or URL slug. Raises on failure."""
    client = _get_anthropic_client()
    message = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=48,
        messages=[{
            "role": "user",
            "content": (
                "In one sentence, describe what this link is likely about based on its title. "
                "Reply with only the sentence, no preamble.\n\n"
                f"Title: {hint}"
            ),
        }],
    )
    return message.content[0].text.strip()


def categorize_link(summary: str) -> LinkCategory:
    """Ask Claude to assign a LinkCategory to *summary*. Raises on failure."""
    valid_values = ", ".join(c.value for c in LinkCategory)
    client = _get_anthropic_client()
    message = client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=32,
        messages=[{
            "role": "user",
            "content": (
                f"Given the following summary of a web page, choose the single most "
                f"relevant category from this list: {valid_values}.\n"
                "Reply with only the category value, nothing else.\n\n"
                f"Summary: {summary}"
            ),
        }],
    )
    raw = message.content[0].text.strip().lower()
    try:
        return LinkCategory(raw)
    except ValueError:
        logger.warning("Unrecognised category %r, defaulting to OTHER", raw)
        return LinkCategory.OTHER
