# Import base tool
from agent.tools.base_tool import BaseTool
from agent.tools.tool_manager import ToolManager

# Import file operation tools
from agent.tools.read.read import Read
from agent.tools.write.write import Write
from agent.tools.edit.edit import Edit
from agent.tools.bash.bash import Bash
from agent.tools.ls.ls import Ls
from agent.tools.send.send import Send

# Import memory tools
from agent.tools.memory.memory_search import MemorySearchTool
from agent.tools.memory.memory_get import MemoryGetTool

# Import tools with optional dependencies
def _import_optional_tools():
    """Import tools that have optional dependencies"""
    from common.log import logger
    tools = {}
    
    # EnvConfig Tool (requires python-dotenv)
    try:
        from agent.tools.env_config.env_config import EnvConfig
        tools['EnvConfig'] = EnvConfig
    except ImportError as e:
        logger.error(
            f"[Tools] EnvConfig tool not loaded - missing dependency: {e}\n"
            f"  To enable environment variable management, run:\n"
            f"    pip install python-dotenv>=1.0.0"
        )
    except Exception as e:
        logger.error(f"[Tools] EnvConfig tool failed to load: {e}")
    
    # Scheduler Tool (requires croniter)
    try:
        from agent.tools.scheduler.scheduler_tool import SchedulerTool
        tools['SchedulerTool'] = SchedulerTool
    except ImportError as e:
        logger.error(
            f"[Tools] Scheduler tool not loaded - missing dependency: {e}\n"
            f"  To enable scheduled tasks, run:\n"
            f"    pip install croniter>=2.0.0"
        )
    except Exception as e:
        logger.error(f"[Tools] Scheduler tool failed to load: {e}")

    # WebSearch Tool (conditionally loaded based on API key availability at init time)
    try:
        from agent.tools.web_search.web_search import WebSearch
        tools['WebSearch'] = WebSearch
    except ImportError as e:
        logger.error(f"[Tools] WebSearch not loaded - missing dependency: {e}")
    except Exception as e:
        logger.error(f"[Tools] WebSearch failed to load: {e}")

    return tools

# Load optional tools
_optional_tools = _import_optional_tools()
EnvConfig = _optional_tools.get('EnvConfig')
SchedulerTool = _optional_tools.get('SchedulerTool')
WebSearch = _optional_tools.get('WebSearch')
GoogleSearch = _optional_tools.get('GoogleSearch')
FileSave = _optional_tools.get('FileSave')
Terminal = _optional_tools.get('Terminal')


# Delayed import for BrowserTool
def _import_browser_tool():
    try:
        from agent.tools.browser.browser_tool import BrowserTool
        return BrowserTool
    except ImportError:
        # Return a placeholder class that will prompt the user to install dependencies when instantiated
        class BrowserToolPlaceholder:
            def __init__(self, *args, **kwargs):
                raise ImportError(
                    "The 'browser-use' package is required to use BrowserTool. "
                    "Please install it with 'pip install browser-use>=0.1.40'."
                )

        return BrowserToolPlaceholder


# Dynamically set BrowserTool
# BrowserTool = _import_browser_tool()

# Export all tools (including optional ones that might be None)
__all__ = [
    'BaseTool',
    'ToolManager',
    'Read',
    'Write',
    'Edit',
    'Bash',
    'Ls',
    'Send',
    'MemorySearchTool',
    'MemoryGetTool',
    'EnvConfig',
    'SchedulerTool',
    'WebSearch',
    # Optional tools (may be None if dependencies not available)
    # 'BrowserTool'
]

"""
Tools module for Agent.
"""
