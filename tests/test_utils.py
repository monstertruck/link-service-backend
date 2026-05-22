"""Unit tests for lib/utils.py."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from lib.utils import (
    _extract_body_text,
    _extract_title,
    _needs_js,
    fetch_page_text,
    fetch_page_title_and_text,
    title_from_url,
)


# ---------------------------------------------------------------------------
# title_from_url
# ---------------------------------------------------------------------------

class TestTitleFromUrl:
    def test_slug_with_hyphens(self):
        assert title_from_url("https://example.com/some-great-article") == "Some Great Article"

    def test_slug_with_underscores(self):
        assert title_from_url("https://example.com/my_first_post") == "My First Post"

    def test_strips_html_extension(self):
        assert title_from_url("https://example.com/posts/my_first_post.html") == "My First Post"

    def test_strips_other_extensions(self):
        assert title_from_url("https://example.com/guide.php") == "Guide"

    def test_no_path_returns_hostname(self):
        assert title_from_url("https://news.ycombinator.com") == "news.ycombinator.com"

    def test_root_path_returns_hostname(self):
        assert title_from_url("https://example.com/") == "example.com"

    def test_nested_path_uses_last_segment(self):
        assert title_from_url("https://example.com/blog/posts/hello-world") == "Hello World"

    def test_mixed_separators(self):
        assert title_from_url("https://example.com/my-great_post") == "My Great Post"


# ---------------------------------------------------------------------------
# _extract_title
# ---------------------------------------------------------------------------

class TestExtractTitle:
    def test_returns_title_text(self):
        html = "<html><head><title>My Page Title</title></head><body></body></html>"
        assert _extract_title(html) == "My Page Title"

    def test_strips_whitespace(self):
        html = "<html><head><title>  Padded Title  </title></head></html>"
        assert _extract_title(html) == "Padded Title"

    def test_returns_none_when_no_title_tag(self):
        html = "<html><head></head><body>No title here</body></html>"
        assert _extract_title(html) is None

    def test_returns_none_for_empty_title(self):
        html = "<html><head><title>   </title></head></html>"
        assert _extract_title(html) is None

    def test_returns_none_for_empty_string(self):
        assert _extract_title("") is None


# ---------------------------------------------------------------------------
# _extract_body_text
# ---------------------------------------------------------------------------

class TestExtractBodyText:
    def test_extracts_main_content(self):
        html = """
        <html><body>
            <nav>Skip me</nav>
            <main>Hello world content here</main>
        </body></html>
        """
        text = _extract_body_text(html)
        assert "Hello world content here" in text
        assert "Skip me" not in text

    def test_prefers_main_over_body(self):
        html = "<html><body><p>Body text</p><main>Main text</main></body></html>"
        assert "Main text" in _extract_body_text(html)

    def test_prefers_article_when_no_main(self):
        html = "<html><body><p>Outside</p><article>Article content</article></body></html>"
        text = _extract_body_text(html)
        assert "Article content" in text

    def test_falls_back_to_body(self):
        html = "<html><body><p>Just body text</p></body></html>"
        assert "Just body text" in _extract_body_text(html)

    def test_strips_script_tags(self):
        html = "<html><body><script>var x = 1;</script><p>Real content</p></body></html>"
        text = _extract_body_text(html)
        assert "var x" not in text
        assert "Real content" in text

    def test_strips_style_tags(self):
        html = "<html><body><style>.foo { color: red }</style><p>Visible</p></body></html>"
        text = _extract_body_text(html)
        assert ".foo" not in text
        assert "Visible" in text

    def test_strips_nav_and_footer(self):
        html = """
        <html><body>
            <nav>Navigation</nav>
            <main>Content</main>
            <footer>Footer stuff</footer>
        </body></html>
        """
        text = _extract_body_text(html)
        assert "Navigation" not in text
        assert "Footer stuff" not in text
        assert "Content" in text

    def test_normalises_whitespace(self):
        html = "<html><body><main>word1    word2\n\nword3</main></body></html>"
        text = _extract_body_text(html)
        assert "  " not in text
        assert "word1 word2 word3" in text

    def test_empty_html_returns_empty_string(self):
        assert _extract_body_text("") == ""


# ---------------------------------------------------------------------------
# _needs_js
# ---------------------------------------------------------------------------

class TestNeedsJs:
    def _html_with_words(self, count: int) -> str:
        words = " ".join(f"word{i}" for i in range(count))
        return f"<html><body><p>{words}</p></body></html>"

    def test_returns_true_when_below_threshold(self):
        assert _needs_js(self._html_with_words(10)) is True

    def test_returns_false_when_above_threshold(self):
        assert _needs_js(self._html_with_words(100)) is False

    def test_returns_true_for_empty_html(self):
        assert _needs_js("") is True

    def test_noise_tags_excluded_from_count(self):
        # 100 words inside a <script> block — should still look empty
        words = " ".join(f"word{i}" for i in range(100))
        html = f"<html><body><script>{words}</script></body></html>"
        assert _needs_js(html) is True


# ---------------------------------------------------------------------------
# fetch_page_text / fetch_page_title_and_text  (async, httpx mocked)
# ---------------------------------------------------------------------------

SAMPLE_HTML = """
<html>
  <head><title>Sample Page</title></head>
  <body>
    <main>{}</main>
  </body>
</html>
""".format(" ".join(f"word{i}" for i in range(100)))


@pytest.mark.asyncio
class TestFetchPageText:
    async def test_returns_body_text_on_success(self):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()

        with patch("lib.utils.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            text = await fetch_page_text("https://example.com")

        assert "word0" in text

    async def test_falls_back_to_playwright_on_http_error(self):
        import httpx as _httpx

        with patch("lib.utils.httpx.AsyncClient") as mock_client_cls, \
             patch("lib.utils._playwright_fetch", new=AsyncMock(return_value=SAMPLE_HTML)):

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=_httpx.HTTPError("fail"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            text = await fetch_page_text("https://example.com")

        assert "word0" in text


@pytest.mark.asyncio
class TestFetchPageTitleAndText:
    async def test_returns_title_and_text(self):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = MagicMock()

        with patch("lib.utils.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            title, text = await fetch_page_title_and_text("https://example.com")

        assert title == "Sample Page"
        assert "word0" in text

    async def test_title_is_none_when_missing(self):
        html_no_title = SAMPLE_HTML.replace("<title>Sample Page</title>", "")
        mock_response = MagicMock()
        mock_response.text = html_no_title
        mock_response.raise_for_status = MagicMock()

        with patch("lib.utils.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            title, _ = await fetch_page_title_and_text("https://example.com")

        assert title is None
