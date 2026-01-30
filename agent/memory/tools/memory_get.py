"""
Memory get tool

Allows agents to read specific sections from memory files
"""

from typing import Dict, Any, Optional
from pathlib import Path
from agent.tools.base_tool import BaseTool
from agent.memory.manager import MemoryManager


class MemoryGetTool(BaseTool):
    """Tool for reading memory file contents"""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize memory get tool
        
        Args:
            memory_manager: MemoryManager instance
        """
        super().__init__()
        self.memory_manager = memory_manager
        self._name = "memory_get"
        self._description = (
            "Read specific memory file content by path and line range. "
            "Use after memory_search to get full context from historical memory files."
        )
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to the memory file (e.g., 'MEMORY.md', 'memory/2024-01-29.md')"
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
    
    async def execute(self, **kwargs) -> str:
        """
        Execute memory file read
        
        Args:
            path: File path
            start_line: Start line
            num_lines: Number of lines
            
        Returns:
            File content
        """
        path = kwargs.get("path")
        start_line = kwargs.get("start_line", 1)
        num_lines = kwargs.get("num_lines")
        
        if not path:
            return "Error: path parameter is required"
        
        try:
            workspace_dir = self.memory_manager.config.get_workspace()
            file_path = workspace_dir / path
            
            if not file_path.exists():
                return f"Error: File not found: {path}"
            
            content = file_path.read_text()
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
            
            return '\n'.join(output)
            
        except Exception as e:
            return f"Error reading memory file: {str(e)}"
