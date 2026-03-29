"""
Browser service - Playwright wrapper managing browser lifecycle and page operations.

Lazily launches a Chromium instance on first use, reuses it across tool calls,
and cleans up on close(). Headless mode is auto-detected based on platform and
display availability.
"""

import os
import sys
import re
import uuid
from typing import Optional, Dict, Any, List

from common.log import logger

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright


# ---------------------------------------------------------------------------
# Snapshot DOM helpers
# ---------------------------------------------------------------------------

# Tags that typically carry useful content for an agent
_INTERACTIVE_TAGS = {
    "a", "button", "input", "textarea", "select", "option",
    "label", "details", "summary",
}
_SEMANTIC_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "li", "td", "th", "caption", "figcaption", "blockquote", "pre", "code",
    "nav", "main", "article", "section", "header", "footer", "form", "table",
    "img", "video", "audio",
}
_KEEP_TAGS = _INTERACTIVE_TAGS | _SEMANTIC_TAGS

_SNAPSHOT_JS = """
() => {
    const KEEP = new Set(%s);
    const INTERACTIVE = new Set(%s);
    const SKIP = new Set(["script","style","noscript","svg","path","meta","link","br","hr"]);
    let refCounter = 0;
    const refMap = {};

    function visible(el) {
        if (!(el instanceof HTMLElement)) return true;
        const st = window.getComputedStyle(el);
        if (st.display === "none" || st.visibility === "hidden") return false;
        if (parseFloat(st.opacity) === 0) return false;
        return true;
    }

    function walk(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            const t = node.textContent.trim();
            return t ? t : null;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) return null;
        const tag = node.tagName.toLowerCase();
        if (SKIP.has(tag)) return null;
        if (!visible(node)) return null;

        const children = [];
        for (const ch of node.childNodes) {
            const r = walk(ch);
            if (r !== null) {
                if (typeof r === "string") children.push(r);
                else children.push(r);
            }
        }

        const keep = KEEP.has(tag);
        if (!keep) {
            // Unwrap: promote children
            if (children.length === 0) return null;
            if (children.length === 1) return children[0];
            return children;
        }

        const obj = { tag };
        if (INTERACTIVE.has(tag)) {
            refCounter++;
            obj.ref = refCounter;
            refMap[refCounter] = node;
        }

        // Attributes
        if (tag === "a" && node.href) obj.href = node.getAttribute("href");
        if (tag === "img") {
            obj.alt = node.alt || "";
            obj.src = node.getAttribute("src") || "";
        }
        if (tag === "input" || tag === "textarea" || tag === "select") {
            obj.type = node.type || "text";
            obj.name = node.name || undefined;
            obj.value = node.value || undefined;
            obj.placeholder = node.placeholder || undefined;
            if (node.disabled) obj.disabled = true;
            if (tag === "input" && node.type === "checkbox") obj.checked = node.checked;
        }
        if (tag === "button") {
            if (node.disabled) obj.disabled = true;
        }
        if (tag === "option") {
            obj.value = node.value;
            if (node.selected) obj.selected = true;
        }
        if (tag === "label" && node.htmlFor) obj.for = node.htmlFor;

        // Role / aria-label
        const role = node.getAttribute("role");
        if (role) obj.role = role;
        const ariaLabel = node.getAttribute("aria-label");
        if (ariaLabel) obj.ariaLabel = ariaLabel;

        // Children
        if (children.length === 1 && typeof children[0] === "string") {
            obj.text = children[0];
        } else if (children.length > 0) {
            obj.children = children;
        }

        return obj;
    }

    // Store refMap on window for later use by click/fill actions
    const result = walk(document.body);
    window.__cowRefMap = refMap;
    return { tree: result, refCount: refCounter };
}
""" % (
    str(list(_KEEP_TAGS)),
    str(list(_INTERACTIVE_TAGS)),
)


def _should_use_headless() -> bool:
    """Decide headless mode: headless on Linux servers without display, headed elsewhere."""
    if sys.platform in ("win32", "darwin"):
        return False
    # Linux: check for display
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return False
    return True


def _flatten_tree(node, indent=0) -> List[str]:
    """Convert snapshot tree to compact text lines for LLM consumption."""
    if node is None:
        return []
    if isinstance(node, str):
        return [" " * indent + node]
    if isinstance(node, list):
        lines = []
        for child in node:
            lines.extend(_flatten_tree(child, indent))
        return lines
    if not isinstance(node, dict):
        return []

    tag = node.get("tag", "?")
    ref = node.get("ref")
    parts = [tag]
    if ref:
        parts[0] = f"[{ref}] {tag}"

    # Inline attributes
    for attr in ("type", "name", "href", "alt", "role", "ariaLabel", "placeholder", "value"):
        val = node.get(attr)
        if val:
            # Truncate long values
            s = str(val)
            if len(s) > 80:
                s = s[:77] + "..."
            parts.append(f'{attr}="{s}"')

    for flag in ("disabled", "checked", "selected"):
        if node.get(flag):
            parts.append(flag)

    prefix = " " * indent
    header = prefix + " ".join(parts)

    text = node.get("text")
    if text:
        # Truncate long text
        if len(text) > 120:
            text = text[:117] + "..."
        header += f": {text}"

    lines = [header]
    children = node.get("children", [])
    for child in children:
        lines.extend(_flatten_tree(child, indent + 2))
    return lines


class BrowserService:
    """Manages a single Playwright browser instance with page operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._headless: Optional[bool] = None
        self._screenshot_dir: Optional[str] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _ensure_browser(self):
        """Lazily launch browser on first use."""
        if self._page and not self._page.is_closed():
            return

        if self._headless is None:
            headless_cfg = self._config.get("headless")
            self._headless = headless_cfg if headless_cfg is not None else _should_use_headless()

        launch_args = ["--disable-dev-shm-usage"]
        if self._headless:
            launch_args.append("--no-sandbox")

        extra_args = self._config.get("launch_args", [])
        if extra_args:
            launch_args.extend(extra_args)

        viewport_w = self._config.get("viewport_width", 1280)
        viewport_h = self._config.get("viewport_height", 720)

        if not self._playwright:
            self._playwright = sync_playwright().start()

        logger.info(f"[Browser] Launching Chromium (headless={self._headless})")
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            args=launch_args,
        )
        self._context = self._browser.new_context(
            viewport={"width": viewport_w, "height": viewport_h},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        self._page = self._context.new_page()
        logger.info("[Browser] Browser ready")

    @property
    def page(self) -> Page:
        self._ensure_browser()
        return self._page

    def close(self):
        """Release all browser resources."""
        try:
            if self._context:
                self._context.close()
        except Exception as e:
            logger.debug(f"[Browser] context close error: {e}")
        try:
            if self._browser:
                self._browser.close()
        except Exception as e:
            logger.debug(f"[Browser] browser close error: {e}")
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            logger.debug(f"[Browser] playwright stop error: {e}")
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        logger.info("[Browser] Browser closed")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def navigate(self, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to a URL and wait for the page to be fully rendered."""
        page = self.page
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            status = resp.status if resp else None
        except Exception as e:
            return {"error": f"Navigation failed: {e}"}

        # Wait for network idle and visual stability
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        # Extra settle time for JS-rendered content (SPA frameworks, animations)
        page.wait_for_timeout(800)

        return {
            "url": page.url,
            "title": page.title(),
            "status": status,
        }

    def snapshot(self, selector: Optional[str] = None) -> str:
        """
        Return a compact text representation of the page DOM for LLM consumption.
        Interactive elements get numeric refs usable in click/fill actions.
        """
        page = self.page
        try:
            target = selector or "body"
            result = page.evaluate(_SNAPSHOT_JS)
        except Exception as e:
            return f"[Snapshot error: {e}]"

        tree = result.get("tree")
        ref_count = result.get("refCount", 0)
        lines = _flatten_tree(tree)

        header = f"Page: {page.title()}  ({page.url})\nInteractive elements: {ref_count}\n---"
        body = "\n".join(lines)

        # Limit output size
        max_chars = self._config.get("snapshot_max_chars", 30000)
        if len(body) > max_chars:
            body = body[:max_chars] + "\n... [snapshot truncated]"

        return f"{header}\n{body}"

    def screenshot(self, full_page: bool = False, cwd: str = "") -> str:
        """Take a screenshot and save to workspace/tmp. Returns file path."""
        page = self.page
        save_dir = self._get_screenshot_dir(cwd)
        filename = f"screenshot_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(save_dir, filename)

        page.screenshot(path=filepath, full_page=full_page)
        logger.info(f"[Browser] Screenshot saved: {filepath}")
        return filepath

    def click(self, ref: Optional[int] = None, selector: Optional[str] = None,
              timeout: int = 5000) -> Dict[str, Any]:
        """Click an element by snapshot ref or CSS selector."""
        page = self.page
        try:
            if ref is not None:
                result = page.evaluate(f"""
                    () => {{
                        const el = window.__cowRefMap && window.__cowRefMap[{ref}];
                        if (!el) return {{ error: "ref {ref} not found. Run snapshot first." }};
                        el.click();
                        return {{ clicked: true, tag: el.tagName.toLowerCase() }};
                    }}
                """)
                if result.get("error"):
                    return result
                page.wait_for_timeout(500)
                return result
            elif selector:
                page.click(selector, timeout=timeout)
                return {"clicked": True, "selector": selector}
            else:
                return {"error": "Provide either ref (from snapshot) or selector"}
        except Exception as e:
            return {"error": f"Click failed: {e}"}

    def fill(self, text: str, ref: Optional[int] = None,
             selector: Optional[str] = None, timeout: int = 5000) -> Dict[str, Any]:
        """Fill text into an input/textarea by snapshot ref or CSS selector."""
        page = self.page
        try:
            if ref is not None:
                result = page.evaluate(f"""
                    () => {{
                        const el = window.__cowRefMap && window.__cowRefMap[{ref}];
                        if (!el) return {{ error: "ref {ref} not found. Run snapshot first." }};
                        el.focus();
                        el.value = "";
                        return {{ tag: el.tagName.toLowerCase(), name: el.name || "" }};
                    }}
                """)
                if result.get("error"):
                    return result
                page.keyboard.type(text)
                return {"filled": True, "ref": ref, "text": text}
            elif selector:
                page.fill(selector, text, timeout=timeout)
                return {"filled": True, "selector": selector, "text": text}
            else:
                return {"error": "Provide either ref (from snapshot) or selector"}
        except Exception as e:
            return {"error": f"Fill failed: {e}"}

    def select(self, value: str, ref: Optional[int] = None,
               selector: Optional[str] = None, timeout: int = 5000) -> Dict[str, Any]:
        """Select an option in a <select> element."""
        page = self.page
        try:
            if ref is not None:
                result = page.evaluate(f"""
                    () => {{
                        const el = window.__cowRefMap && window.__cowRefMap[{ref}];
                        if (!el || el.tagName.toLowerCase() !== "select")
                            return {{ error: "ref {ref} is not a <select> element" }};
                        el.value = {repr(value)};
                        el.dispatchEvent(new Event("change", {{ bubbles: true }}));
                        return {{ selected: true, value: el.value }};
                    }}
                """)
                return result
            elif selector:
                page.select_option(selector, value, timeout=timeout)
                return {"selected": True, "selector": selector, "value": value}
            else:
                return {"error": "Provide either ref (from snapshot) or selector"}
        except Exception as e:
            return {"error": f"Select failed: {e}"}

    def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Scroll the page."""
        page = self.page
        delta_map = {
            "down": (0, amount),
            "up": (0, -amount),
            "right": (amount, 0),
            "left": (-amount, 0),
        }
        dx, dy = delta_map.get(direction, (0, amount))
        try:
            page.mouse.wheel(dx, dy)
            page.wait_for_timeout(300)
            scroll_info = page.evaluate("""
                () => ({
                    scrollX: window.scrollX,
                    scrollY: window.scrollY,
                    scrollHeight: document.documentElement.scrollHeight,
                    clientHeight: document.documentElement.clientHeight
                })
            """)
            return {"scrolled": direction, "amount": amount, **scroll_info}
        except Exception as e:
            return {"error": f"Scroll failed: {e}"}

    def wait(self, selector: Optional[str] = None, timeout: int = 5000,
             state: str = "visible") -> Dict[str, Any]:
        """Wait for a selector to appear or a fixed timeout."""
        page = self.page
        try:
            if selector:
                page.wait_for_selector(selector, timeout=timeout, state=state)
                return {"waited": True, "selector": selector, "state": state}
            else:
                page.wait_for_timeout(timeout)
                return {"waited": True, "timeout_ms": timeout}
        except Exception as e:
            return {"error": f"Wait failed: {e}"}

    def go_back(self) -> Dict[str, Any]:
        page = self.page
        try:
            page.go_back(wait_until="domcontentloaded", timeout=10000)
            return {"url": page.url, "title": page.title()}
        except Exception as e:
            return {"error": f"Go back failed: {e}"}

    def go_forward(self) -> Dict[str, Any]:
        page = self.page
        try:
            page.go_forward(wait_until="domcontentloaded", timeout=10000)
            return {"url": page.url, "title": page.title()}
        except Exception as e:
            return {"error": f"Go forward failed: {e}"}

    def get_text(self, selector: str) -> Dict[str, Any]:
        """Get text content of an element."""
        page = self.page
        try:
            text = page.text_content(selector, timeout=5000)
            return {"text": text or ""}
        except Exception as e:
            return {"error": f"Get text failed: {e}"}

    def evaluate(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript in the page context."""
        page = self.page
        try:
            result = page.evaluate(script)
            return {"result": result}
        except Exception as e:
            return {"error": f"Evaluate failed: {e}"}

    def press(self, key: str) -> Dict[str, Any]:
        """Press a keyboard key (e.g. Enter, Tab, Escape)."""
        page = self.page
        try:
            page.keyboard.press(key)
            page.wait_for_timeout(300)
            return {"pressed": key}
        except Exception as e:
            return {"error": f"Press failed: {e}"}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_screenshot_dir(self, cwd: str = "") -> str:
        if self._screenshot_dir and os.path.isdir(self._screenshot_dir):
            return self._screenshot_dir
        base = cwd or os.getcwd()
        d = os.path.join(base, "tmp")
        os.makedirs(d, exist_ok=True)
        self._screenshot_dir = d
        return d
