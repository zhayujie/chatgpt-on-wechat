"""
Find tool - Search for files by glob pattern
"""

import os
import glob as glob_module
from typing import Dict, Any, List

from agent.tools.base_tool import BaseTool, ToolResult
from agent.tools.utils.truncate import truncate_head, format_size, DEFAULT_MAX_BYTES


DEFAULT_LIMIT = 1000


class Find(BaseTool):
    """Tool for finding files by pattern"""
    
    name: str = "find"
    description: str = f"Search for files by glob pattern. Returns matching file paths relative to the search directory. Respects .gitignore. Output is truncated to {DEFAULT_LIMIT} results or {DEFAULT_MAX_BYTES // 1024}KB (whichever is hit first)."
    
    params: dict = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match files, e.g. '*.ts', '**/*.json', or 'src/**/*.spec.ts'"
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current directory)"
            },
            "limit": {
                "type": "integer",
                "description": f"Maximum number of results (default: {DEFAULT_LIMIT})"
            }
        },
        "required": ["pattern"]
    }
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.cwd = self.config.get("cwd", os.getcwd())
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute file search
        
        :param args: Search parameters
        :return: Search results or error
        """
        pattern = args.get("pattern", "").strip()
        search_path = args.get("path", ".").strip()
        limit = args.get("limit", DEFAULT_LIMIT)
        
        if not pattern:
            return ToolResult.fail("Error: pattern parameter is required")
        
        # Resolve search path
        absolute_path = self._resolve_path(search_path)
        
        if not os.path.exists(absolute_path):
            return ToolResult.fail(f"Error: Path not found: {search_path}")
        
        if not os.path.isdir(absolute_path):
            return ToolResult.fail(f"Error: Not a directory: {search_path}")
        
        try:
            # Load .gitignore patterns
            ignore_patterns = self._load_gitignore(absolute_path)
            
            # Search for files
            results = []
            search_pattern = os.path.join(absolute_path, pattern)
            
            # Use glob with recursive support
            for file_path in glob_module.glob(search_pattern, recursive=True):
                # Skip if matches ignore patterns
                if self._should_ignore(file_path, absolute_path, ignore_patterns):
                    continue
                
                # Get relative path
                relative_path = os.path.relpath(file_path, absolute_path)
                
                # Add trailing slash for directories
                if os.path.isdir(file_path):
                    relative_path += '/'
                
                results.append(relative_path)
                
                if len(results) >= limit:
                    break
            
            if not results:
                return ToolResult.success({"message": "No files found matching pattern", "files": []})
            
            # Sort results
            results.sort()
            
            # Format output
            raw_output = '\n'.join(results)
            truncation = truncate_head(raw_output, max_lines=999999)  # Only limit by bytes
            
            output = truncation.content
            details = {}
            notices = []
            
            result_limit_reached = len(results) >= limit
            if result_limit_reached:
                notices.append(f"{limit} results limit reached. Use limit={limit * 2} for more, or refine pattern")
                details["result_limit_reached"] = limit
            
            if truncation.truncated:
                notices.append(f"{format_size(DEFAULT_MAX_BYTES)} limit reached")
                details["truncation"] = truncation.to_dict()
            
            if notices:
                output += f"\n\n[{'. '.join(notices)}]"
            
            return ToolResult.success({
                "output": output,
                "file_count": len(results),
                "details": details if details else None
            })
            
        except Exception as e:
            return ToolResult.fail(f"Error executing find: {str(e)}")
    
    def _resolve_path(self, path: str) -> str:
        """Resolve path to absolute path"""
        # Expand ~ to user home directory
        path = os.path.expanduser(path)
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.cwd, path))
    
    def _load_gitignore(self, directory: str) -> List[str]:
        """Load .gitignore patterns from directory"""
        patterns = []
        gitignore_path = os.path.join(directory, '.gitignore')
        
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            patterns.append(line)
            except:
                pass
        
        # Add common ignore patterns
        patterns.extend([
            '.git',
            '__pycache__',
            '*.pyc',
            'node_modules',
            '.DS_Store'
        ])
        
        return patterns
    
    def _should_ignore(self, file_path: str, base_path: str, patterns: List[str]) -> bool:
        """Check if file should be ignored based on patterns"""
        relative_path = os.path.relpath(file_path, base_path)
        
        for pattern in patterns:
            # Simple pattern matching
            if pattern in relative_path:
                return True
            
            # Check if it's a directory pattern
            if pattern.endswith('/'):
                if relative_path.startswith(pattern.rstrip('/')):
                    return True
        
        return False
