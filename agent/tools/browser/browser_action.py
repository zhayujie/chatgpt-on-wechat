class BrowserAction:
    """Base class for browser actions"""
    code = ""
    description = ""


class Navigate(BrowserAction):
    """Navigate to a URL in the current tab"""
    code = "navigate"
    description = "Navigate to URL in the current tab"


class ClickElement(BrowserAction):
    """Click an element on the page"""
    code = "click_element"
    description = "Click element"


class ExtractContent(BrowserAction):
    """Extract content from the page"""
    code = "extract_content"
    description = "Extract the page content to retrieve specific information for a goal"


class InputText(BrowserAction):
    """Input text into an element"""
    code = "input_text"
    description = "Input text into a input interactive element"


class ScrollDown(BrowserAction):
    """Scroll down the page"""
    code = "scroll_down"
    description = "Scroll down the page by pixel amount"


class ScrollUp(BrowserAction):
    """Scroll up the page"""
    code = "scroll_up"
    description = "Scroll up the page by pixel amount - if no amount is specified, scroll up one page"


class OpenTab(BrowserAction):
    """Open a URL in a new tab"""
    code = "open_tab"
    description = "Open url in new tab"


class SwitchTab(BrowserAction):
    """Switch to a tab"""
    code = "switch_tab"
    description = "Switched to tab"


class SendKeys(BrowserAction):
    """Switch to a tab"""
    code = "send_keys"
    description = "Send strings of special keyboard keys like Escape, Backspace, Insert, PageDown, Delete, Enter, " \
                  "ArrowRight, ArrowUp, etc"
