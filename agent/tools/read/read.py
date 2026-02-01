"""
Read tool - Read file contents
Supports text files, images (jpg, png, gif, webp), and PDF files
"""

import os
from typing import Dict, Any
from pathlib import Path

from agent.tools.base_tool import BaseTool, ToolResult
from agent.tools.utils.truncate import truncate_head, format_size, DEFAULT_MAX_LINES, DEFAULT_MAX_BYTES


class Read(BaseTool):
    """Tool for reading file contents"""
    
    name: str = "read"
    description: str = f"Read the contents of a file. Supports text files, PDF files, and images (jpg, png, gif, webp). For text files, output is truncated to {DEFAULT_MAX_LINES} lines or {DEFAULT_MAX_BYTES // 1024}KB (whichever is hit first). Use offset/limit for large files."
    
    params: dict = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read. IMPORTANT: Relative paths are based on workspace directory. To access files outside workspace, use absolute paths starting with ~ or /."
            },
            "offset": {
                "type": "integer",
                "description": "Line number to start reading from (1-indexed, optional)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of lines to read (optional)"
            }
        },
        "required": ["path"]
    }
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.cwd = self.config.get("cwd", os.getcwd())
        # Supported image formats
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        # Supported PDF format
        self.pdf_extensions = {'.pdf'}
    
    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute file read operation
        
        :param args: Contains file path and optional offset/limit parameters
        :return: File content or error message
        """
        path = args.get("path", "").strip()
        offset = args.get("offset")
        limit = args.get("limit")
        
        if not path:
            return ToolResult.fail("Error: path parameter is required")
        
        # Resolve path
        absolute_path = self._resolve_path(path)
        
        # Check if file exists
        if not os.path.exists(absolute_path):
            # Provide helpful hint if using relative path
            if not os.path.isabs(path) and not path.startswith('~'):
                return ToolResult.fail(
                    f"Error: File not found: {path}\n"
                    f"Resolved to: {absolute_path}\n"
                    f"Hint: Relative paths are based on workspace ({self.cwd}). For files outside workspace, use absolute paths."
                )
            return ToolResult.fail(f"Error: File not found: {path}")
        
        # Check if readable
        if not os.access(absolute_path, os.R_OK):
            return ToolResult.fail(f"Error: File is not readable: {path}")
        
        # Check file type
        file_ext = Path(absolute_path).suffix.lower()
        
        # Check if image
        if file_ext in self.image_extensions:
            return self._read_image(absolute_path, file_ext)
        
        # Check if PDF
        if file_ext in self.pdf_extensions:
            return self._read_pdf(absolute_path, path, offset, limit)
        
        # Read text file
        return self._read_text(absolute_path, path, offset, limit)
    
    def _resolve_path(self, path: str) -> str:
        """
        Resolve path to absolute path
        
        :param path: Relative or absolute path
        :return: Absolute path
        """
        # Expand ~ to user home directory
        path = os.path.expanduser(path)
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.cwd, path))
    
    def _read_image(self, absolute_path: str, file_ext: str) -> ToolResult:
        """
        Read image file
        
        :param absolute_path: Absolute path to the image file
        :param file_ext: File extension
        :return: Result containing image information
        """
        try:
            # Read image file
            with open(absolute_path, 'rb') as f:
                image_data = f.read()
            
            # Get file size
            file_size = len(image_data)
            
            # Return image information (actual image data can be base64 encoded when needed)
            import base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Determine MIME type
            mime_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_type_map.get(file_ext, 'image/jpeg')
            
            result = {
                "type": "image",
                "mime_type": mime_type,
                "size": file_size,
                "size_formatted": format_size(file_size),
                "data": base64_data  # Base64 encoded image data
            }
            
            return ToolResult.success(result)
            
        except Exception as e:
            return ToolResult.fail(f"Error reading image file: {str(e)}")
    
    def _read_text(self, absolute_path: str, display_path: str, offset: int = None, limit: int = None) -> ToolResult:
        """
        Read text file
        
        :param absolute_path: Absolute path to the file
        :param display_path: Path to display
        :param offset: Starting line number (1-indexed)
        :param limit: Maximum number of lines to read
        :return: File content or error message
        """
        try:
            # Read file
            with open(absolute_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            all_lines = content.split('\n')
            total_file_lines = len(all_lines)
            
            # Apply offset (if specified)
            start_line = 0
            if offset is not None:
                start_line = max(0, offset - 1)  # Convert to 0-indexed
                if start_line >= total_file_lines:
                    return ToolResult.fail(
                        f"Error: Offset {offset} is beyond end of file ({total_file_lines} lines total)"
                    )
            
            start_line_display = start_line + 1  # For display (1-indexed)
            
            # If user specified limit, use it
            selected_content = content
            user_limited_lines = None
            if limit is not None:
                end_line = min(start_line + limit, total_file_lines)
                selected_content = '\n'.join(all_lines[start_line:end_line])
                user_limited_lines = end_line - start_line
            elif offset is not None:
                selected_content = '\n'.join(all_lines[start_line:])
            
            # Apply truncation (considering line count and byte limits)
            truncation = truncate_head(selected_content)
            
            output_text = ""
            details = {}
            
            if truncation.first_line_exceeds_limit:
                # First line exceeds 30KB limit
                first_line_size = format_size(len(all_lines[start_line].encode('utf-8')))
                output_text = f"[Line {start_line_display} is {first_line_size}, exceeds {format_size(DEFAULT_MAX_BYTES)} limit. Use bash tool to read: head -c {DEFAULT_MAX_BYTES} {display_path} | tail -n +{start_line_display}]"
                details["truncation"] = truncation.to_dict()
            elif truncation.truncated:
                # Truncation occurred
                end_line_display = start_line_display + truncation.output_lines - 1
                next_offset = end_line_display + 1
                
                output_text = truncation.content
                
                if truncation.truncated_by == "lines":
                    output_text += f"\n\n[Showing lines {start_line_display}-{end_line_display} of {total_file_lines}. Use offset={next_offset} to continue.]"
                else:
                    output_text += f"\n\n[Showing lines {start_line_display}-{end_line_display} of {total_file_lines} ({format_size(DEFAULT_MAX_BYTES)} limit). Use offset={next_offset} to continue.]"
                
                details["truncation"] = truncation.to_dict()
            elif user_limited_lines is not None and start_line + user_limited_lines < total_file_lines:
                # User specified limit, more content available, but no truncation
                remaining = total_file_lines - (start_line + user_limited_lines)
                next_offset = start_line + user_limited_lines + 1
                
                output_text = truncation.content
                output_text += f"\n\n[{remaining} more lines in file. Use offset={next_offset} to continue.]"
            else:
                # No truncation, no exceeding user limit
                output_text = truncation.content
            
            result = {
                "content": output_text,
                "total_lines": total_file_lines,
                "start_line": start_line_display,
                "output_lines": truncation.output_lines
            }
            
            if details:
                result["details"] = details
            
            return ToolResult.success(result)
            
        except UnicodeDecodeError:
            return ToolResult.fail(f"Error: File is not a valid text file (encoding error): {display_path}")
        except Exception as e:
            return ToolResult.fail(f"Error reading file: {str(e)}")
    
    def _read_pdf(self, absolute_path: str, display_path: str, offset: int = None, limit: int = None) -> ToolResult:
        """
        Read PDF file content
        
        :param absolute_path: Absolute path to the file
        :param display_path: Path to display
        :param offset: Starting line number (1-indexed)
        :param limit: Maximum number of lines to read
        :return: PDF text content or error message
        """
        try:
            # Try to import pypdf
            try:
                from pypdf import PdfReader
            except ImportError:
                return ToolResult.fail(
                    "Error: pypdf library not installed. Install with: pip install pypdf"
                )
            
            # Read PDF
            reader = PdfReader(absolute_path)
            total_pages = len(reader.pages)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")
            
            if not text_parts:
                return ToolResult.success({
                    "content": f"[PDF file with {total_pages} pages, but no text content could be extracted]",
                    "total_pages": total_pages,
                    "message": "PDF may contain only images or be encrypted"
                })
            
            # Merge all text
            full_content = "\n\n".join(text_parts)
            all_lines = full_content.split('\n')
            total_lines = len(all_lines)
            
            # Apply offset and limit (same logic as text files)
            start_line = 0
            if offset is not None:
                start_line = max(0, offset - 1)
                if start_line >= total_lines:
                    return ToolResult.fail(
                        f"Error: Offset {offset} is beyond end of content ({total_lines} lines total)"
                    )
            
            start_line_display = start_line + 1
            
            selected_content = full_content
            user_limited_lines = None
            if limit is not None:
                end_line = min(start_line + limit, total_lines)
                selected_content = '\n'.join(all_lines[start_line:end_line])
                user_limited_lines = end_line - start_line
            elif offset is not None:
                selected_content = '\n'.join(all_lines[start_line:])
            
            # Apply truncation
            truncation = truncate_head(selected_content)
            
            output_text = ""
            details = {}
            
            if truncation.truncated:
                end_line_display = start_line_display + truncation.output_lines - 1
                next_offset = end_line_display + 1
                
                output_text = truncation.content
                
                if truncation.truncated_by == "lines":
                    output_text += f"\n\n[Showing lines {start_line_display}-{end_line_display} of {total_lines}. Use offset={next_offset} to continue.]"
                else:
                    output_text += f"\n\n[Showing lines {start_line_display}-{end_line_display} of {total_lines} ({format_size(DEFAULT_MAX_BYTES)} limit). Use offset={next_offset} to continue.]"
                
                details["truncation"] = truncation.to_dict()
            elif user_limited_lines is not None and start_line + user_limited_lines < total_lines:
                remaining = total_lines - (start_line + user_limited_lines)
                next_offset = start_line + user_limited_lines + 1
                
                output_text = truncation.content
                output_text += f"\n\n[{remaining} more lines in file. Use offset={next_offset} to continue.]"
            else:
                output_text = truncation.content
            
            result = {
                "content": output_text,
                "total_pages": total_pages,
                "total_lines": total_lines,
                "start_line": start_line_display,
                "output_lines": truncation.output_lines
            }
            
            if details:
                result["details"] = details
            
            return ToolResult.success(result)
            
        except Exception as e:
            return ToolResult.fail(f"Error reading PDF file: {str(e)}")
