"""
Web Fetch tool - Fetch and extract readable content from URLs
Supports HTML to Markdown/Text conversion using Mozilla's Readability
"""

import os
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from agent.tools.base_tool import BaseTool, ToolResult
from common.log import logger


class WebFetch(BaseTool):
    """Tool for fetching and extracting readable content from web pages"""
    
    name: str = "web_fetch"
    description: str = "Fetch and extract readable content from a URL (HTML → markdown/text). Use for lightweight page access without browser automation. Returns title, content, and metadata."
    
    params: dict = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "HTTP or HTTPS URL to fetch"
            },
            "extract_mode": {
                "type": "string",
                "description": "Extraction mode: 'markdown' (default) or 'text'",
                "enum": ["markdown", "text"],
                "default": "markdown"
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximum characters to return (default: 50000)",
                "minimum": 100,
                "default": 50000
            }
        },
        "required": ["url"]
    }
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
        self.max_redirects = self.config.get("max_redirects", 3)
        self.user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Setup session with retry strategy
        self.session = self._create_session()
        
        # Check if readability-lxml is available
        self.readability_available = self._check_readability()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        # Retry strategy - handles failed requests, not redirects
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        
        # HTTPAdapter handles retries; requests handles redirects via allow_redirects
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set max redirects on session
        session.max_redirects = self.max_redirects
        
        return session
    
    def _check_readability(self) -> bool:
        """Check if readability-lxml is available"""
        try:
            from readability import Document
            return True
        except ImportError:
            logger.warning(
                "readability-lxml not installed. Install with: pip install readability-lxml\n"
                "Falling back to basic HTML extraction."
            )
            return False
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute web fetch operation
        
        :param args: Contains url, extract_mode, and max_chars parameters
        :return: Extracted content or error message
        """
        url = args.get("url", "").strip()
        extract_mode = args.get("extract_mode", "markdown").lower()
        max_chars = args.get("max_chars", 50000)
        
        if not url:
            return ToolResult.fail("Error: url parameter is required")
        
        # Validate URL
        if not self._is_valid_url(url):
            return ToolResult.fail(f"Error: Invalid URL (must be http or https): {url}")
        
        # Validate extract_mode
        if extract_mode not in ["markdown", "text"]:
            extract_mode = "markdown"
        
        # Validate max_chars
        if not isinstance(max_chars, int) or max_chars < 100:
            max_chars = 50000
        
        try:
            # Fetch the URL
            response = self._fetch_url(url)
            
            # Extract content
            result = self._extract_content(
                html=response.text,
                url=response.url,
                status_code=response.status_code,
                content_type=response.headers.get("content-type", ""),
                extract_mode=extract_mode,
                max_chars=max_chars
            )
            
            return ToolResult.success(result)
            
        except requests.exceptions.Timeout:
            return ToolResult.fail(f"Error: Request timeout after {self.timeout} seconds")
        except requests.exceptions.TooManyRedirects:
            return ToolResult.fail(f"Error: Too many redirects (limit: {self.max_redirects})")
        except requests.exceptions.RequestException as e:
            return ToolResult.fail(f"Error fetching URL: {str(e)}")
        except Exception as e:
            logger.error(f"Web fetch error: {e}", exc_info=True)
            return ToolResult.fail(f"Error: {str(e)}")
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return result.scheme in ["http", "https"] and bool(result.netloc)
        except Exception:
            return False
    
    def _fetch_url(self, url: str) -> requests.Response:
        """
        Fetch URL with proper headers and error handling
        
        :param url: URL to fetch
        :return: Response object
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN,zh;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        # Note: requests library handles redirects automatically
        # The max_redirects is set in the session's adapter (HTTPAdapter)
        response = self.session.get(
            url,
            headers=headers,
            timeout=self.timeout,
            allow_redirects=True
        )
        
        response.raise_for_status()
        return response
    
    def _extract_content(
        self,
        html: str,
        url: str,
        status_code: int,
        content_type: str,
        extract_mode: str,
        max_chars: int
    ) -> Dict[str, Any]:
        """
        Extract readable content from HTML
        
        :param html: HTML content
        :param url: Original URL
        :param status_code: HTTP status code
        :param content_type: Content type header
        :param extract_mode: 'markdown' or 'text'
        :param max_chars: Maximum characters to return
        :return: Extracted content and metadata
        """
        # Check content type
        if "text/html" not in content_type.lower():
            # Non-HTML content
            text = html[:max_chars]
            truncated = len(html) > max_chars
            
            return {
                "url": url,
                "status": status_code,
                "content_type": content_type,
                "extractor": "raw",
                "text": text,
                "length": len(text),
                "truncated": truncated,
                "message": f"Non-HTML content (type: {content_type})"
            }
        
        # Extract readable content from HTML
        if self.readability_available:
            return self._extract_with_readability(
                html, url, status_code, content_type, extract_mode, max_chars
            )
        else:
            return self._extract_basic(
                html, url, status_code, content_type, extract_mode, max_chars
            )
    
    def _extract_with_readability(
        self,
        html: str,
        url: str,
        status_code: int,
        content_type: str,
        extract_mode: str,
        max_chars: int
    ) -> Dict[str, Any]:
        """Extract content using Mozilla's Readability"""
        try:
            from readability import Document
            
            # Parse with Readability
            doc = Document(html)
            title = doc.title()
            content_html = doc.summary()
            
            # Convert to markdown or text
            if extract_mode == "markdown":
                text = self._html_to_markdown(content_html)
            else:
                text = self._html_to_text(content_html)
            
            # Truncate if needed
            truncated = len(text) > max_chars
            if truncated:
                text = text[:max_chars]
            
            return {
                "url": url,
                "status": status_code,
                "content_type": content_type,
                "title": title,
                "extractor": "readability",
                "extract_mode": extract_mode,
                "text": text,
                "length": len(text),
                "truncated": truncated
            }
            
        except Exception as e:
            logger.warning(f"Readability extraction failed: {e}")
            # Fallback to basic extraction
            return self._extract_basic(
                html, url, status_code, content_type, extract_mode, max_chars
            )
    
    def _extract_basic(
        self,
        html: str,
        url: str,
        status_code: int,
        content_type: str,
        extract_mode: str,
        max_chars: int
    ) -> Dict[str, Any]:
        """Basic HTML extraction without Readability"""
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Untitled"
        
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Truncate if needed
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars]
        
        return {
            "url": url,
            "status": status_code,
            "content_type": content_type,
            "title": title,
            "extractor": "basic",
            "extract_mode": extract_mode,
            "text": text,
            "length": len(text),
            "truncated": truncated,
            "warning": "Using basic extraction. Install readability-lxml for better results."
        }
    
    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown (basic implementation)"""
        try:
            # Try to use html2text if available
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0  # Don't wrap lines
            return h.handle(html)
        except ImportError:
            # Fallback to basic conversion
            return self._html_to_text(html)
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert common tags to text equivalents
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<p[^>]*>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<h[1-6][^>]*>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</h[1-6]>', '\n', text, flags=re.IGNORECASE)
        
        # Remove all other HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        text = text.strip()
        
        return text
    
    def close(self):
        """Close the session"""
        if hasattr(self, 'session'):
            self.session.close()
