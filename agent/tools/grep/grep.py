"""
Grep tool - Search file contents for patterns
Uses ripgrep (rg) for fast searching
"""

import os
import re
import subprocess
import json
from typing import Dict, Any, List, Optional

from agent.tools.base_tool import BaseTool, ToolResult
from agent.tools.utils.truncate import (
    truncate_head, truncate_line, format_size,
    DEFAULT_MAX_BYTES, GREP_MAX_LINE_LENGTH
)


DEFAULT_LIMIT = 100


class Grep(BaseTool):
    """Tool for searching file contents"""
    
    name: str = "grep"
    description: str = f"Search file contents for a pattern. Returns matching lines with file paths and line numbers. Respects .gitignore. Output is truncated to {DEFAULT_LIMIT} matches or {DEFAULT_MAX_BYTES // 1024}KB (whichever is hit first). Long lines are truncated to {GREP_MAX_LINE_LENGTH} chars."
    
    params: dict = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Search pattern (regex or literal string)"
            },
            "path": {
                "type": "string",
                "description": "Directory or file to search (default: current directory)"
            },
            "glob": {
                "type": "string",
                "description": "Filter files by glob pattern, e.g. '*.ts' or '**/*.spec.ts'"
            },
            "ignoreCase": {
                "type": "boolean",
                "description": "Case-insensitive search (default: false)"
            },
            "literal": {
                "type": "boolean",
                "description": "Treat pattern as literal string instead of regex (default: false)"
            },
            "context": {
                "type": "integer",
                "description": "Number of lines to show before and after each match (default: 0)"
            },
            "limit": {
                "type": "integer",
                "description": f"Maximum number of matches to return (default: {DEFAULT_LIMIT})"
            }
        },
        "required": ["pattern"]
    }
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.cwd = self.config.get("cwd", os.getcwd())
        self.rg_path = self._find_ripgrep()
    
    def _find_ripgrep(self) -> Optional[str]:
        """Find ripgrep executable"""
        try:
            result = subprocess.run(['which', 'rg'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute grep search
        
        :param args: Search parameters
        :return: Search results or error
        """
        if not self.rg_path:
            return ToolResult.fail("Error: ripgrep (rg) is not installed. Please install it first.")
        
        pattern = args.get("pattern", "").strip()
        search_path = args.get("path", ".").strip()
        glob = args.get("glob")
        ignore_case = args.get("ignoreCase", False)
        literal = args.get("literal", False)
        context = args.get("context", 0)
        limit = args.get("limit", DEFAULT_LIMIT)
        
        if not pattern:
            return ToolResult.fail("Error: pattern parameter is required")
        
        # Resolve search path
        absolute_path = self._resolve_path(search_path)
        
        if not os.path.exists(absolute_path):
            return ToolResult.fail(f"Error: Path not found: {search_path}")
        
        # Build ripgrep command
        cmd = [
            self.rg_path,
            '--json',
            '--line-number',
            '--color=never',
            '--hidden'
        ]
        
        if ignore_case:
            cmd.append('--ignore-case')
        
        if literal:
            cmd.append('--fixed-strings')
        
        if glob:
            cmd.extend(['--glob', glob])
        
        cmd.extend([pattern, absolute_path])
        
        try:
            # Execute ripgrep
            result = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            matches = []
            match_count = 0
            
            for line in result.stdout.splitlines():
                if not line.strip():
                    continue
                
                try:
                    event = json.loads(line)
                    if event.get('type') == 'match':
                        data = event.get('data', {})
                        file_path = data.get('path', {}).get('text')
                        line_number = data.get('line_number')
                        
                        if file_path and line_number:
                            matches.append({
                                'file': file_path,
                                'line': line_number
                            })
                            match_count += 1
                            
                            if match_count >= limit:
                                break
                except json.JSONDecodeError:
                    continue
            
            if match_count == 0:
                return ToolResult.success({"message": "No matches found", "matches": []})
            
            # Format output with context
            output_lines = []
            lines_truncated = False
            is_directory = os.path.isdir(absolute_path)
            
            for match in matches:
                file_path = match['file']
                line_number = match['line']
                
                # Format file path
                if is_directory:
                    relative_path = os.path.relpath(file_path, absolute_path)
                else:
                    relative_path = os.path.basename(file_path)
                
                # Read file and get context
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_lines = f.read().split('\n')
                    
                    # Calculate context range
                    start = max(0, line_number - 1 - context) if context > 0 else line_number - 1
                    end = min(len(file_lines), line_number + context) if context > 0 else line_number
                    
                    # Format lines with context
                    for i in range(start, end):
                        line_text = file_lines[i].replace('\r', '')
                        
                        # Truncate long lines
                        truncated_text, was_truncated = truncate_line(line_text)
                        if was_truncated:
                            lines_truncated = True
                        
                        # Format output
                        current_line = i + 1
                        if current_line == line_number:
                            output_lines.append(f"{relative_path}:{current_line}: {truncated_text}")
                        else:
                            output_lines.append(f"{relative_path}-{current_line}- {truncated_text}")
                
                except Exception:
                    output_lines.append(f"{relative_path}:{line_number}: (unable to read file)")
            
            # Apply byte truncation
            raw_output = '\n'.join(output_lines)
            truncation = truncate_head(raw_output, max_lines=999999)  # Only limit by bytes
            
            output = truncation.content
            details = {}
            notices = []
            
            if match_count >= limit:
                notices.append(f"{limit} matches limit reached. Use limit={limit * 2} for more, or refine pattern")
                details["match_limit_reached"] = limit
            
            if truncation.truncated:
                notices.append(f"{format_size(DEFAULT_MAX_BYTES)} limit reached")
                details["truncation"] = truncation.to_dict()
            
            if lines_truncated:
                notices.append(f"Some lines truncated to {GREP_MAX_LINE_LENGTH} chars. Use read tool to see full lines")
                details["lines_truncated"] = True
            
            if notices:
                output += f"\n\n[{'. '.join(notices)}]"
            
            return ToolResult.success({
                "output": output,
                "match_count": match_count,
                "details": details if details else None
            })
            
        except subprocess.TimeoutExpired:
            return ToolResult.fail("Error: Search timed out after 30 seconds")
        except Exception as e:
            return ToolResult.fail(f"Error executing grep: {str(e)}")
    
    def _resolve_path(self, path: str) -> str:
        """Resolve path to absolute path"""
        # Expand ~ to user home directory
        path = os.path.expanduser(path)
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.cwd, path))
