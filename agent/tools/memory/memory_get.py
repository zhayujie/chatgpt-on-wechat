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

        from config import conf
        if conf().get("knowledge", True):
            self.description = (
                "Read specific content from memory or knowledge files. "
                "Use this to get full context from a memory file, knowledge page, or specific line range."
            )
            self.params = {**self.params}
            self.params["properties"] = {**self.params["properties"]}
            self.params["properties"]["path"] = {
                "type": "string",
                "description": "Relative path to the memory or knowledge file (e.g. 'MEMORY.md', 'memory/2026-01-01.md', 'knowledge/concepts/moe.md')"
            }
    
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
            result = self.memory_manager.read_document_range(
                path=path,
                start_line=start_line,
                num_lines=num_lines,
            )
            metadata = result.get("metadata") or {}
            section_title = metadata.get("section_title") or ""
            section_path = metadata.get("section_path") or ""
            page_number = metadata.get("page_number")
            output = [
                f"File: {result['path']}",
                f"Lines: {result['start_line']}-{result['end_line']} (total: {result['total_lines']})",
                f"Citation: {result['citation']}",
                "",
            ]

            if result.get("title"):
                output.append(f"Title: {result['title']}")
            if page_number is not None:
                output.append(f"Page: {page_number}")
            if section_path:
                output.append(f"Section Path: {section_path}")
            elif section_title:
                output.append(f"Section: {section_title}")
            output.extend([
                "",
                result["content"],
            ])

            return ToolResult.success('\n'.join(output))
            
        except Exception as e:
            return ToolResult.fail(f"Error reading memory file: {str(e)}")
