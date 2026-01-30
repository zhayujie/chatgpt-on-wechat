import asyncio
from typing import Any, Dict
import json
import re
import os
import platform
from browser_use import Browser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from agent.tools.base_tool import BaseTool, ToolResult
from agent.tools.browser.browser_action import *
from agent.models import LLMRequest
from agent.models.model_factory import ModelFactory
from browser_use.dom.service import DomService
from common.log import logger


# Use lazy import, only import when actually used
def _import_browser_use():
    try:
        import browser_use
        return browser_use
    except ImportError:
        raise ImportError(
            "The 'browser-use' package is required to use BrowserTool. "
            "Please install it with 'pip install browser-use>=0.1.40' or "
            "'pip install agentmesh-sdk[full]'."
        )


def _get_action_prompt():
    action_classes = [Navigate, ClickElement, ExtractContent, InputText, OpenTab, SwitchTab, ScrollDown, ScrollUp,
                      SendKeys]
    action_prompt = ""
    for action_class in action_classes:
        action_prompt += f"{action_class.code}: {action_class.description}\n"
    return action_prompt.strip()


def _header_less() -> bool:
    if platform.system() == "Linux" and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return True
    return False


class BrowserTool(BaseTool):
    name: str = "browser"
    description: str = "A tool to perform browser operations like navigating to URLs, element interaction, " \
                       "and extracting content."
    params: dict = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": f"The browser operation to perform: \n{_get_action_prompt()}"
            },
            "url": {
                "type": "string",
                "description": f"The URL to navigate to (required for '{Navigate.code}', '{OpenTab.code}' actions). "
            },
            "goal": {
                "type": "string",
                "description": f"The goal of extracting page content (required for '{ExtractContent.code}' action)."
            },
            "text": {
                "type": "string",
                "description": f"Text to type (required for '{InputText.code}' action)."
            },
            "index": {
                "type": "integer",
                "description": f"Element index (required for '{ClickElement.code}', '{InputText.code}' actions)",
            },
            "tab_id": {
                "type": "integer",
                "description": f"Page tab ID (required for '{SwitchTab.code}' action)",
            },
            "scroll_amount": {
                "type": "integer",
                "description": f"The number of pixels to scroll (required for '{ScrollDown.code}', '{ScrollUp.code}' action)."
            },
            "keys": {
                "type": "string",
                "description": f"Keys to send (required for '{SendKeys.code}' action)"
            }
        },
        "required": ["operation"]
    }

    # Class variable to ensure only one browser instance is created
    browser = None
    browser_context: BrowserContext = None
    dom_service: DomService = None
    _initialized = False

    # Adding an event loop variable
    _event_loop = None

    def __init__(self):
        # Only import during initialization, not at module level
        self.browser_use = _import_browser_use()
        # Do not initialize the browser in the constructor, but initialize it on the first execution
        pass

    async def _init_browser(self) -> BrowserContext:
        """Ensure the browser is initialized"""
        if not BrowserTool._initialized:
            os.environ['BROWSER_USE_LOGGING_LEVEL'] = 'error'
            print("Initializing browser...")
            # Initialize the browser synchronously
            BrowserTool.browser = Browser(BrowserConfig(headless=_header_less(),
                                                        disable_security=True))
            context_config = BrowserContextConfig()
            context_config.highlight_elements = True
            BrowserTool.browser_context = await BrowserTool.browser.new_context(context_config)
            BrowserTool._initialized = True
            print("Browser initialized successfully")
            BrowserTool.dom_service = DomService(await BrowserTool.browser_context.get_current_page())
        return BrowserTool.browser_context

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        Execute browser operations based on the provided arguments.
        
        :param params: Dictionary containing the action and related parameters
        :return: Result of the browser operation
        """
        # Ensure browser_use is imported
        if not hasattr(self, 'browser_use'):
            self.browser_use = _import_browser_use()
        action = params.get("operation", "").lower()

        try:
            # Use a single event loop
            if BrowserTool._event_loop is None:
                BrowserTool._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(BrowserTool._event_loop)
            # Run tasks in the existing event loop
            return BrowserTool._event_loop.run_until_complete(self._execute_async(action, params))
        except Exception as e:
            print(f"Error executing browser action: {e}")
            return ToolResult.fail(result=f"Error executing browser action: {str(e)}")

    async def _get_page_state(self, context: BrowserContext):
        state = await self._get_state(context)
        include_attributes = ["img", "div", "button", "input"]
        elements = state.element_tree.clickable_elements_to_string(include_attributes)
        pattern = r'\[\d+\]<[^>]+\/>'
        # Find all matching elements
        interactive_elements = re.findall(pattern, elements)
        page_state = {
            "url": state.url,
            "title": state.title,
            "pixels_above": getattr(state, "pixels_above", 0),
            "pixels_below": getattr(state, "pixels_below", 0),
            "tabs": [tab.model_dump() for tab in state.tabs],
            "interactive_elements": interactive_elements,
        }
        return page_state

    async def _get_state(self, context: BrowserContext, cache_clickable_elements_hashes=True):
        try:
            return await context.get_state()
        except TypeError:
            return await context.get_state(cache_clickable_elements_hashes=cache_clickable_elements_hashes)

    async def _get_page_info(self, context: BrowserContext):
        page_state = await self._get_page_state(context)
        state_str = f"""## Current browser state
The following is the information of the current browser page. Each serial number in interactive_elements represents the element index:
{json.dumps(page_state, indent=4, ensure_ascii=False)} 
"""
        return state_str

    async def _execute_async(self, action: str, params: Dict[str, Any]) -> ToolResult:
        """Asynchronously execute browser operations"""
        # Use the browser context from the class variable
        context = await self._init_browser()

        if action == Navigate.code:
            url = params.get("url")
            if not url:
                return ToolResult.fail(result="URL is required for navigate action")
            if url.startswith("/"):
                url = f"file://{url}"
            print(f"Navigating to {url}...")
            page = await context.get_current_page()
            await page.goto(url)
            await page.wait_for_load_state()
            state = await self._get_page_info(context)
            # print(state)
            print(f"Navigation complete")
            return ToolResult.success(result=f"Navigated to {url}", ext_data=state)

        elif action == OpenTab.code:
            url = params.get("url")
            if url.startswith("/"):
                url = f"file://{url}"
            await context.create_new_tab(url)
            msg = f"Opened new tab with {url}"
            return ToolResult.success(result=msg)

        elif action == ExtractContent.code:
            try:
                goal = params.get("goal")
                page = await context.get_current_page()
                if params.get("url"):
                    await page.goto(params.get("url"))
                    await page.wait_for_load_state()
                import markdownify
                content = markdownify.markdownify(await page.content())
                elements = await self._get_page_state(context)
                prompt = f"Your task is to extract the content of the page. You will be given a page and a goal and you should extract all relevant information around this goal from the page. If the goal is vague, " \
                         f"summarize the page. Respond in json format. elements: {elements.get('interactive_elements')}, extraction goal: {goal}, Page: {content},"
                request = LLMRequest(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    json_format=True
                )
                model = self.model or ModelFactory().get_model(model_name="gpt-4o")
                response = model.call(request)
                if response.success:
                    extract_content = response.data["choices"][0]["message"]["content"]
                    print(f"Extract from page: {extract_content}")
                    return ToolResult.success(result=f"Extract from page: {extract_content}",
                                              ext_data=await self._get_page_info(context))
                else:
                    return ToolResult.fail(result=f"Extract from page failed: {response.get_error_msg()}")
            except Exception as e:
                logger.error(e)

        elif action == ClickElement.code:
            index = params.get("index")
            element = await context.get_dom_element_by_index(index)
            await context._click_element_node(element)
            msg = f"Clicked element at index {index}"
            print(msg)
            return ToolResult.success(result=msg, ext_data=await self._get_page_info(context))

        elif action == InputText.code:
            index = params.get("index")
            text = params.get("text")
            element = await context.get_dom_element_by_index(index)
            await context._input_text_element_node(element, text)
            await asyncio.sleep(1)
            msg = f"Input text into element successfully, index: {index}, text: {text}"
            return ToolResult.success(result=msg, ext_data=await self._get_page_info(context))

        elif action == SwitchTab.code:
            tab_id = params.get("tab_id")
            print(f"Switch tab, tab_id={tab_id}")
            await context.switch_to_tab(tab_id)
            page = await context.get_current_page()
            await page.wait_for_load_state()
            msg = f"Switched to tab {tab_id}"
            return ToolResult.success(result=msg, ext_data=await self._get_page_info(context))

        elif action in [ScrollDown.code, ScrollUp.code]:
            scroll_amount = params.get("scroll_amount")
            if not scroll_amount:
                scroll_amount = context.config.browser_window_size["height"]
            print(f"Scrolling by {scroll_amount} pixels")
            scroll_amount = scroll_amount if action == ScrollDown.code else (scroll_amount * -1)
            await context.execute_javascript(f"window.scrollBy(0, {scroll_amount});")
            msg = f"{action} by {scroll_amount} pixels"
            return ToolResult.success(result=msg, ext_data=await self._get_page_info(context))

        elif action == SendKeys.code:
            keys = params.get("keys")
            page = await context.get_current_page()
            await page.keyboard.press(keys)
            msg = f"Sent keys: {keys}"
            print(msg)
            return ToolResult(output=f"Sent keys: {keys}")

        else:
            msg = "Failed to operate the browser"
            return ToolResult.fail(result=msg)

    def close(self):
        """
        Close browser resources.
        This method handles the asynchronous closing of browser and browser context.
        """
        if not BrowserTool._initialized:
            return

        try:
            # Use the existing event loop to close browser resources
            if BrowserTool._event_loop is not None:
                # Define the async close function
                async def close_browser_async():
                    if BrowserTool.browser_context is not None:
                        try:
                            await BrowserTool.browser_context.close()
                        except Exception as e:
                            logger.error(f"Error closing browser context: {e}")

                    if BrowserTool.browser is not None:
                        try:
                            await BrowserTool.browser.close()
                        except Exception as e:
                            logger.error(f"Error closing browser: {e}")

                    # Reset the initialized flag
                    BrowserTool._initialized = False
                    BrowserTool.browser = None
                    BrowserTool.browser_context = None
                    BrowserTool.dom_service = None

                # Run the async close function in the existing event loop
                BrowserTool._event_loop.run_until_complete(close_browser_async())

                # Close the event loop
                BrowserTool._event_loop.close()
                BrowserTool._event_loop = None
        except Exception as e:
            print(f"Error during browser cleanup: {e}")
