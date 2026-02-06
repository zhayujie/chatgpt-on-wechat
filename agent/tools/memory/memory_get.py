"""
Memory get tool

Allows agents to read specific sections from memory files
"""

from agent.tools.base_tool import BaseTool


class MemoryGetTool(BaseTool):
    """Tool for reading memory file contents"""
    
    name: str = "memory_get"
    description: str = (
        "Read specific content from memory files. "
        "Use this to get full context from a memory file or specific line range."
    )
    params: dict = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to the memory file (e.g. 'MEMORY.md', 'memory/2026-01-01.md')"
            },
            "start_line": {
                "type": "integer",
                "description": "Starting line number (optional, default: 1)",
                "default": 1
            },
            "num_lines": {
                "type": "integer",
                "description": "Number of lines to read (optional, reads all if not specified)"
            }
        },
        "required": ["path"]
    }
    
    def __init__(self, memory_manager):
        """
        Initialize memory get tool
        
        Args:
            memory_manager: MemoryManager instance
        """
        super().__init__()
        self.memory_manager = memory_manager
    
    def execute(self, args: dict):
        """
        Execute memory file read
        
        Args:
            args: Dictionary with path, start_line, num_lines
            
        Returns:
            ToolResult with file content
        """
        from agent.tools.base_tool import ToolResult
        
        path = args.get("path")
        start_line = args.get("start_line", 1)
        num_lines = args.get("num_lines")
        
        if not path:
            return ToolResult.fail("Error: path parameter is required")
        
        try:
            workspace_dir = self.memory_manager.config.get_workspace()
            
            # Auto-prepend memory/ if not present and not absolute path
            # Exception: MEMORY.md is in the root directory
            if not path.startswith('memory/') and not path.startswith('/') and path != 'MEMORY.md':
                path = f'memory/{path}'
            
            file_path = workspace_dir / path
            
            if not file_path.exists():
                return ToolResult.fail(f"Error: File not found: {path}")
            
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Handle line range
            if start_line < 1:
                start_line = 1
            
            start_idx = start_line - 1
            
            if num_lines:
                end_idx = start_idx + num_lines
                selected_lines = lines[start_idx:end_idx]
            else:
                selected_lines = lines[start_idx:]
            
            result = '\n'.join(selected_lines)
            
            # Add metadata
            total_lines = len(lines)
            shown_lines = len(selected_lines)
            
            output = [
                f"File: {path}",
                f"Lines: {start_line}-{start_line + shown_lines - 1} (total: {total_lines})",
                "",
                result
            ]
            
            return ToolResult.success('\n'.join(output))
            
        except Exception as e:
            return ToolResult.fail(f"Error reading memory file: {str(e)}")
