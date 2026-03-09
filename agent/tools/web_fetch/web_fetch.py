"""
Web Fetch tool - Fetch and extract readable content from web pages.
"""

import re
from typing import Dict, Any
from urllib.parse import urlparse

import requests

from agent.tools.base_tool import BaseTool, ToolResult
from common.log import logger


DEFAULT_TIMEOUT = 10

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class WebFetch(BaseTool):
    """Tool for fetching and extracting readable content from web pages"""

    name: str = "web_fetch"
    description: str = (
        "Fetch and extract readable text content from a web page URL. "
    )

    params: dict = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The HTTP/HTTPS URL to fetch"
            }
        },
        "required": ["url"]
    }

    def __init__(self, config: dict = None):
        self.config = config or {}

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        url = args.get("url", "").strip()
        if not url:
            return ToolResult.fail("Error: 'url' parameter is required")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return ToolResult.fail("Error: Invalid URL (must start with http:// or https://)")

        try:
            response = requests.get(
                url,
                headers=DEFAULT_HEADERS,
                timeout=DEFAULT_TIMEOUT,
                allow_redirects=True,
            )
            response.raise_for_status()
        except requests.Timeout:
            return ToolResult.fail(f"Error: Request timed out after {DEFAULT_TIMEOUT}s")
        except requests.ConnectionError:
            return ToolResult.fail(f"Error: Failed to connect to {parsed.netloc}")
        except requests.HTTPError as e:
            return ToolResult.fail(f"Error: HTTP {e.response.status_code} for URL: {url}")
        except Exception as e:
            return ToolResult.fail(f"Error: Failed to fetch URL: {e}")

        html = response.text
        title = self._extract_title(html)
        text = self._extract_text(html)

        return ToolResult.success(f"Title: {title}\n\nContent:\n{text}")

    @staticmethod
    def _extract_title(html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else "Untitled"

    @staticmethod
    def _extract_text(html: str) -> str:
        # Remove script and style blocks
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.IGNORECASE | re.DOTALL)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Decode common HTML entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
        # Collapse whitespace: multiple spaces/tabs -> single space, multiple newlines -> double newline
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace per line
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(lines)
        return text.strip()
