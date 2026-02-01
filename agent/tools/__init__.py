# Import base tool
from agent.tools.base_tool import BaseTool
from agent.tools.tool_manager import ToolManager

# Import file operation tools
from agent.tools.read.read import Read
from agent.tools.write.write import Write
from agent.tools.edit.edit import Edit
from agent.tools.bash.bash import Bash
from agent.tools.ls.ls import Ls

# Import memory tools
from agent.tools.memory.memory_search import MemorySearchTool
from agent.tools.memory.memory_get import MemoryGetTool

# Import tools with optional dependencies
def _import_optional_tools():
    """Import tools that have optional dependencies"""
    tools = {}
    
    # Google Search (requires requests)
    try:
        from agent.tools.google_search.google_search import GoogleSearch
        tools['GoogleSearch'] = GoogleSearch
    except ImportError:
        pass
    
    # File Save (may have dependencies)
    try:
        from agent.tools.file_save.file_save import FileSave
        tools['FileSave'] = FileSave
    except ImportError:
        pass
    
    # Terminal (basic, should work)
    try:
        from agent.tools.terminal.terminal import Terminal
        tools['Terminal'] = Terminal
    except ImportError:
        pass
    
    return tools

# Load optional tools
_optional_tools = _import_optional_tools()
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
BrowserTool = _import_browser_tool()

# Export all tools (including optional ones that might be None)
__all__ = [
    'BaseTool',
    'ToolManager',
    'Read',
    'Write',
    'Edit',
    'Bash',
    'Ls',
    'MemorySearchTool',
    'MemoryGetTool',
    # Optional tools (may be None if dependencies not available)
    'GoogleSearch',
    'FileSave',
    'Terminal',
    'BrowserTool'
]

"""
Tools module for Agent.
"""
