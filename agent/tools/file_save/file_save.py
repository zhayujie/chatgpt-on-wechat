import os
import time
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from agent.tools.base_tool import BaseTool, ToolResult, ToolStage
from agent.models import LLMRequest
from common.log import logger


class FileSave(BaseTool):
    """Tool for saving content to files in the workspace directory."""

    name = "file_save"
    description = "Save the agent's output to a file in the workspace directory. Content is automatically extracted from the agent's previous outputs."

    # Set as post-process stage tool
    stage = ToolStage.POST_PROCESS

    params = {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "Optional. The name of the file to save. If not provided, a name will be generated based on the content."
            },
            "file_type": {
                "type": "string",
                "description": "Optional. The type/extension of the file (e.g., 'txt', 'md', 'py', 'java'). If not provided, it will be inferred from the content."
            },
            "extract_code": {
                "type": "boolean",
                "description": "Optional. If true, will attempt to extract code blocks from the content. Default is false."
            }
        },
        "required": []  # No required fields, as everything can be extracted from context
    }

    def __init__(self):
        self.context = None
        self.config = {}
        self.workspace_dir = Path("workspace")

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        Save content to a file in the workspace directory.
        
        :param params: The parameters for the file output operation.
        :return: Result of the operation.
        """
        # Extract content from context
        if not hasattr(self, 'context') or not self.context:
            return ToolResult.fail("Error: No context available to extract content from.")

        content = self._extract_content_from_context()

        # If no content could be extracted, return error
        if not content:
            return ToolResult.fail("Error: Couldn't extract content from context.")

        # Use model to determine file parameters
        try:
            task_dir = self._get_task_dir_from_context()
            file_name, file_type, extract_code = self._get_file_params_from_model(content)
        except Exception as e:
            logger.error(f"Error determining file parameters: {str(e)}")
            # Fall back to manual parameter extraction
            task_dir = params.get("task_dir") or self._get_task_id_from_context() or f"task_{int(time.time())}"
            file_name = params.get("file_name") or self._infer_file_name(content)
            file_type = params.get("file_type") or self._infer_file_type(content)
            extract_code = params.get("extract_code", False)

        # Get team_name from context
        team_name = self._get_team_name_from_context() or "default_team"

        # Create directory structure
        task_dir_path = self.workspace_dir / team_name / task_dir
        task_dir_path.mkdir(parents=True, exist_ok=True)

        if extract_code:
            # Save the complete content as markdown
            md_file_name = f"{file_name}.md"
            md_file_path = task_dir_path / md_file_name

            # Write content to file
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return self._handle_multiple_code_blocks(content)

        # Ensure file_name has the correct extension
        if file_type and not file_name.endswith(f".{file_type}"):
            file_name = f"{file_name}.{file_type}"

        # Create the full file path
        file_path = task_dir_path / file_name

        # Get absolute path for storage in team_context
        abs_file_path = file_path.absolute()

        try:
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update the current agent's final_answer to include file information
            if hasattr(self.context, 'team_context'):
                # Store with absolute path in team_context
                self.context.team_context.agent_outputs[-1].output += f"\n\nSaved file: {abs_file_path}"

            return ToolResult.success({
                "status": "success",
                "file_path": str(file_path)  # Return relative path in result
            })

        except Exception as e:
            return ToolResult.fail(f"Error saving file: {str(e)}")

    def _handle_multiple_code_blocks(self, content: str) -> ToolResult:
        """
        Handle content with multiple code blocks, extracting and saving each as a separate file.

        :param content: The content containing multiple code blocks
        :return: Result of the operation
        """
        # Extract code blocks with context (including potential file name information)
        code_blocks_with_context = self._extract_code_blocks_with_context(content)

        if not code_blocks_with_context:
            return ToolResult.fail("No code blocks found in the content.")

        # Get task directory and team name
        task_dir = self._get_task_dir_from_context() or f"task_{int(time.time())}"
        team_name = self._get_team_name_from_context() or "default_team"

        # Create directory structure
        task_dir_path = self.workspace_dir / team_name / task_dir
        task_dir_path.mkdir(parents=True, exist_ok=True)

        saved_files = []

        for block_with_context in code_blocks_with_context:
            try:
                # Use model to determine file name for this code block
                block_file_name, block_file_type = self._get_filename_for_code_block(block_with_context)

                # Clean the code block (remove md code markers)
                clean_code = self._clean_code_block(block_with_context)

                # Ensure file_name has the correct extension
                if block_file_type and not block_file_name.endswith(f".{block_file_type}"):
                    block_file_name = f"{block_file_name}.{block_file_type}"

                # Create the full file path (no subdirectories)
                file_path = task_dir_path / block_file_name

                # Get absolute path for storage in team_context
                abs_file_path = file_path.absolute()

                # Write content to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(clean_code)

                saved_files.append({
                    "file_path": str(file_path),
                    "abs_file_path": str(abs_file_path),  # Store absolute path for internal use
                    "file_name": block_file_name,
                    "size": len(clean_code),
                    "status": "success",
                    "type": "code"
                })

            except Exception as e:
                logger.error(f"Error saving code block: {str(e)}")
                # Continue with the next block even if this one fails

        if not saved_files:
            return ToolResult.fail("Failed to save any code blocks.")

        # Update the current agent's final_answer to include files information
        if hasattr(self, 'context') and self.context:
            # If the agent has a final_answer attribute, append the files info to it
            if hasattr(self.context, 'team_context'):
                # Use relative paths for display
                display_info = f"\n\nSaved files to {task_dir_path}:\n" + "\n".join(
                    [f"- {f['file_path']}" for f in saved_files])

                # Check if we need to append the info
                if not self.context.team_context.agent_outputs[-1].output.endswith(display_info):
                    # Store with absolute paths in team_context
                    abs_info = f"\n\nSaved files to {task_dir_path.absolute()}:\n" + "\n".join(
                        [f"- {f['abs_file_path']}" for f in saved_files])
                    self.context.team_context.agent_outputs[-1].output += abs_info

        result = {
            "status": "success",
            "files": [{"file_path": f["file_path"]} for f in saved_files]
        }

        return ToolResult.success(result)

    def _extract_code_blocks_with_context(self, content: str) -> list:
        """
        Extract code blocks from content, including context lines before the block.

        :param content: The content to extract code blocks from
        :return: List of code blocks with context
        """
        # Check if content starts with <!DOCTYPE or <html - likely a full HTML file
        if content.strip().startswith(("<!DOCTYPE", "<html", "<?xml")):
            return [content]  # Return the entire content as a single block

        # Split content into lines
        lines = content.split('\n')

        blocks = []
        in_code_block = False
        current_block = []
        context_lines = []

        # Check if there are any code block markers in the content
        if not re.search(r'```\w+', content):
            # If no code block markers and content looks like code, return the entire content
            if self._is_likely_code(content):
                return [content]

        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    current_block.append(line)
                    # Only add blocks that have a language specified
                    block_content = '\n'.join(current_block)
                    if re.search(r'```\w+', current_block[0]):
                        # Combine context with code block
                        blocks.append('\n'.join(context_lines + current_block))
                    current_block = []
                    context_lines = []
                    in_code_block = False
                else:
                    # Start of code block - check if it has a language specified
                    if re.search(r'```\w+', line) and not re.search(r'```language=\s*$', line):
                        # Start of code block with language
                        in_code_block = True
                        current_block = [line]
                        # Keep only the last few context lines
                        context_lines = context_lines[-5:] if context_lines else []

            elif in_code_block:
                current_block.append(line)
            else:
                # Store context lines when not in a code block
                context_lines.append(line)

        return blocks

    def _get_filename_for_code_block(self, block_with_context: str) -> Tuple[str, str]:
        """
        Determine the file name for a code block.

        :param block_with_context: The code block with context lines
        :return: Tuple of (file_name, file_type)
        """
        # Define common code file extensions
        COMMON_CODE_EXTENSIONS = {
            'py', 'js', 'java', 'c', 'cpp', 'h', 'hpp', 'cs', 'go', 'rb', 'php',
            'html', 'css', 'ts', 'jsx', 'tsx', 'vue', 'sh', 'sql', 'json', 'xml',
            'yaml', 'yml', 'md', 'rs', 'swift', 'kt', 'scala', 'pl', 'r', 'lua'
        }

        # Split the block into lines to examine only the context around code block markers
        lines = block_with_context.split('\n')

        # Find the code block start marker line index
        start_marker_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('```') and not line.strip() == '```':
                start_marker_idx = i
                break

        if start_marker_idx == -1:
            # No code block marker found
            return "", ""

        # Extract the language from the code block marker
        code_marker = lines[start_marker_idx].strip()
        language = ""
        if len(code_marker) > 3:
            language = code_marker[3:].strip().split('=')[0].strip()

        # Define the context range (5 lines before and 2 after the marker)
        context_start = max(0, start_marker_idx - 5)
        context_end = min(len(lines), start_marker_idx + 3)

        # Extract only the relevant context lines
        context_lines = lines[context_start:context_end]

        # First, check for explicit file headers like "## filename.ext"
        for line in context_lines:
            # Match patterns like "## filename.ext" or "# filename.ext"
            header_match = re.search(r'^\s*#{1,6}\s+([a-zA-Z0-9_-]+\.[a-zA-Z0-9]+)\s*$', line)
            if header_match:
                file_name = header_match.group(1)
                file_type = os.path.splitext(file_name)[1].lstrip('.')
                if file_type in COMMON_CODE_EXTENSIONS:
                    return os.path.splitext(file_name)[0], file_type

        # Simple patterns to match explicit file names in the context
        file_patterns = [
            # Match explicit file names in headers or text
            r'(?:file|filename)[:=\s]+[\'"]?([a-zA-Z0-9_-]+\.[a-zA-Z0-9]+)[\'"]?',
            # Match language=filename.ext in code markers
            r'language=([a-zA-Z0-9_-]+\.[a-zA-Z0-9]+)',
            # Match standalone filenames with extensions
            r'\b([a-zA-Z0-9_-]+\.(py|js|java|c|cpp|h|hpp|cs|go|rb|php|html|css|ts|jsx|tsx|vue|sh|sql|json|xml|yaml|yml|md|rs|swift|kt|scala|pl|r|lua))\b',
            # Match file paths in comments
            r'#\s*([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)'
        ]

        # Check each context line for file name patterns
        for line in context_lines:
            line = line.strip()
            for pattern in file_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            # If the match is a tuple (filename, extension)
                            file_name = match[0]
                            file_type = match[1]
                            # Verify it's not a code reference like Direction.DOWN
                            if not any(keyword in file_name for keyword in ['class.', 'enum.', 'import.']):
                                return os.path.splitext(file_name)[0], file_type
                        else:
                            # If the match is a string (full filename)
                            file_name = match
                            file_type = os.path.splitext(file_name)[1].lstrip('.')
                            # Verify it's not a code reference
                            if file_type in COMMON_CODE_EXTENSIONS and not any(
                                    keyword in file_name for keyword in ['class.', 'enum.', 'import.']):
                                return os.path.splitext(file_name)[0], file_type

        # If no explicit file name found, use LLM to infer from code content
        # Extract the code content
        code_content = block_with_context

        # Get the first 20 lines of code for LLM analysis
        code_lines = code_content.split('\n')
        code_preview = '\n'.join(code_lines[:20])

        # Get the model to use
        model_to_use = None
        if hasattr(self, 'context') and self.context:
            if hasattr(self.context, 'model') and self.context.model:
                model_to_use = self.context.model
            elif hasattr(self.context, 'team_context') and self.context.team_context:
                if hasattr(self.context.team_context, 'model') and self.context.team_context.model:
                    model_to_use = self.context.team_context.model

        # If no model is available in context, use the tool's model
        if not model_to_use and hasattr(self, 'model') and self.model:
            model_to_use = self.model

        if model_to_use:
            # Prepare a prompt for the model
            prompt = f"""Analyze the following code and determine the most appropriate file name and file type/extension.
The file name should be descriptive but concise, using snake_case (lowercase with underscores).
The file type should be a standard file extension (e.g., py, js, html, css, java).

Code preview (first 20 lines):
{code_preview}

Return your answer in JSON format with these fields:
- file_name: The suggested file name (without extension)
- file_type: The suggested file extension

JSON response:"""

            # Create a request to the model
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                json_format=True
            )

            try:
                response = model_to_use.call(request)

                if not response.is_error:
                    # Clean the JSON response
                    json_content = self._clean_json_response(response.data["choices"][0]["message"]["content"])
                    result = json.loads(json_content)

                    file_name = result.get("file_name", "")
                    file_type = result.get("file_type", "")

                    if file_name and file_type:
                        return file_name, file_type
            except Exception as e:
                logger.error(f"Error using model to determine file name: {str(e)}")

        # If we still don't have a file name, use the language as file type
        if language and language in COMMON_CODE_EXTENSIONS:
            timestamp = int(time.time())
            return f"code_{timestamp}", language

        # If all else fails, return empty strings
        return "", ""

    def _clean_json_response(self, text: str) -> str:
        """
        Clean JSON response from LLM by removing markdown code block markers.
        
        :param text: The text containing JSON possibly wrapped in markdown code blocks
        :return: Clean JSON string
        """
        # Remove markdown code block markers if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            # Find the first newline to skip the language identifier line
            first_newline = text.find('\n')
            if first_newline != -1:
                text = text[first_newline + 1:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def _clean_code_block(self, block_with_context: str) -> str:
        """
        Clean a code block by removing markdown code markers and context lines.
        
        :param block_with_context: Code block with context lines
        :return: Clean code ready for execution
        """
        # Check if this is a full HTML or XML document
        if block_with_context.strip().startswith(("<!DOCTYPE", "<html", "<?xml")):
            return block_with_context

        # Find the code block
        code_block_match = re.search(r'```(?:\w+)?(?:[:=][^\n]+)?\n([\s\S]*?)\n```', block_with_context)

        if code_block_match:
            return code_block_match.group(1)

        # If no match found, try to extract anything between ``` markers
        lines = block_with_context.split('\n')
        start_idx = None
        end_idx = None

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if start_idx is None:
                    start_idx = i
                else:
                    end_idx = i
                    break

        if start_idx is not None and end_idx is not None:
            # Extract the code between the markers, excluding the markers themselves
            code_lines = lines[start_idx + 1:end_idx]
            return '\n'.join(code_lines)

        # If all else fails, return the original content
        return block_with_context

    def _get_file_params_from_model(self, content, model=None):
        """
        Use LLM to determine if the content is code and suggest appropriate file parameters.
        
        Args:
            content: The content to analyze
            model: Optional model to use for the analysis
            
        Returns:
            tuple: (file_name, file_type, extract_code) for backward compatibility
        """
        if model is None:
            model = self.model

        if not model:
            # Default fallback if no model is available
            return "output", "txt", False

        prompt = f"""
        Analyze the following content and determine:
        1. Is this primarily code implementation (where most of the content consists of code blocks)?
        2. What would be an appropriate filename and file extension?
        
        Content to analyze:    ```
        {content[:500]}  # Only show first 500 chars to avoid token limits    ```
        
        {"..." if len(content) > 500 else ""}
        
        Respond in JSON format only with the following structure:
        {{
            "is_code": true/false,  # Whether this is primarily code implementation
            "filename": "suggested_filename",  # Don't include extension, english words
            "extension": "appropriate_extension"  # Don't include the dot, e.g., "md", "py", "js"
        }}
        """

        try:
            # Create a request to the model
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                json_format=True
            )

            # Call the model using the standard interface
            response = model.call(request)

            if response.is_error:
                logger.warning(f"Error from model: {response.error_message}")
                raise Exception(f"Model error: {response.error_message}")

            # Extract JSON from response
            result = response.data["choices"][0]["message"]["content"]

            # Clean the JSON response
            result = self._clean_json_response(result)

            # Parse the JSON
            params = json.loads(result)

            # For backward compatibility, return tuple format
            file_name = params.get("filename", "output")
            # Remove dot from extension if present
            file_type = params.get("extension", "md").lstrip(".")
            extract_code = params.get("is_code", False)

            return file_name, file_type, extract_code
        except Exception as e:
            logger.warning(f"Error getting file parameters from model: {e}")
            # Default fallback
            return "output", "md", False

    def _get_team_name_from_context(self) -> Optional[str]:
        """
        Get team name from the agent's context.

        :return: Team name or None if not found
        """
        if hasattr(self, 'context') and self.context:
            # Try to get team name from team_context
            if hasattr(self.context, 'team_context') and self.context.team_context:
                return self.context.team_context.name

            # Try direct team_name attribute
            if hasattr(self.context, 'name'):
                return self.context.name

        return None

    def _get_task_id_from_context(self) -> Optional[str]:
        """
        Get task ID from the agent's context.

        :return: Task ID or None if not found
        """
        if hasattr(self, 'context') and self.context:
            # Try to get task ID from task object
            if hasattr(self.context, 'task') and self.context.task:
                return self.context.task.id

            # Try team_context's task
            if hasattr(self.context, 'team_context') and self.context.team_context:
                if hasattr(self.context.team_context, 'task') and self.context.team_context.task:
                    return self.context.team_context.task.id

        return None

    def _get_task_dir_from_context(self) -> Optional[str]:
        """
        Get task directory name from the team context.

        :return: Task directory name or None if not found
        """
        if hasattr(self, 'context') and self.context:
            # Try to get from team_context
            if hasattr(self.context, 'team_context') and self.context.team_context:
                if hasattr(self.context.team_context, 'task_short_name') and self.context.team_context.task_short_name:
                    return self.context.team_context.task_short_name

        # Fall back to task ID if available
        return self._get_task_id_from_context()

    def _extract_content_from_context(self) -> str:
        """
        Extract content from the agent's context.

        :return: Extracted content
        """
        # Check if we have access to the agent's context
        if not hasattr(self, 'context') or not self.context:
            return ""

        # Try to get the most recent final answer from the agent
        if hasattr(self.context, 'final_answer') and self.context.final_answer:
            return self.context.final_answer

        # Try to get the most recent final answer from team context
        if hasattr(self.context, 'team_context') and self.context.team_context:
            if hasattr(self.context.team_context, 'agent_outputs') and self.context.team_context.agent_outputs:
                latest_output = self.context.team_context.agent_outputs[-1].output
                return latest_output

        # If we have action history, try to get the most recent final answer
        if hasattr(self.context, 'action_history') and self.context.action_history:
            for action in reversed(self.context.action_history):
                if "final_answer" in action and action["final_answer"]:
                    return action["final_answer"]

        return ""

    def _extract_code_blocks(self, content: str) -> str:
        """
        Extract code blocks from markdown content.

        :param content: The content to extract code blocks from
        :return: Extracted code blocks
        """
        # Pattern to match markdown code blocks
        code_block_pattern = r'```(?:\w+)?\n([\s\S]*?)\n```'

        # Find all code blocks
        code_blocks = re.findall(code_block_pattern, content)

        if code_blocks:
            # Join all code blocks with newlines
            return '\n\n'.join(code_blocks)

        return content  # Return original content if no code blocks found

    def _infer_file_name(self, content: str) -> str:
        """
        Infer a file name from the content.
        
        :param content: The content to analyze.
        :return: A suggested file name.
        """
        # Check for title patterns in markdown
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            # Convert title to a valid filename
            title = title_match.group(1).strip()
            return self._sanitize_filename(title)

        # Check for class/function definitions in code
        code_match = re.search(r'(class|def|function)\s+(\w+)', content)
        if code_match:
            return self._sanitize_filename(code_match.group(2))

        # Default name based on content type
        if self._is_likely_code(content):
            return "code"
        elif self._is_likely_markdown(content):
            return "document"
        elif self._is_likely_json(content):
            return "data"
        else:
            return "output"

    def _infer_file_type(self, content: str) -> str:
        """
        Infer the file type/extension from the content.
        
        :param content: The content to analyze.
        :return: A suggested file extension.
        """
        # Check for common programming language patterns
        if re.search(r'(import\s+[a-zA-Z0-9_]+|from\s+[a-zA-Z0-9_\.]+\s+import)', content):
            return "py"  # Python
        elif re.search(r'(public\s+class|private\s+class|protected\s+class)', content):
            return "java"  # Java
        elif re.search(r'(function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=)', content):
            return "js"  # JavaScript
        elif re.search(r'(<html|<body|<div|<p>)', content):
            return "html"  # HTML
        elif re.search(r'(#include\s+<\w+\.h>|int\s+main\s*\()', content):
            return "cpp"  # C/C++

        # Check for markdown
        if self._is_likely_markdown(content):
            return "md"

        # Check for JSON
        if self._is_likely_json(content):
            return "json"

        # Default to text
        return "txt"

    def _is_likely_code(self, content: str) -> bool:
        """Check if the content is likely code."""
        # First check for common HTML/XML patterns
        if content.strip().startswith(("<!DOCTYPE", "<html", "<?xml", "<head", "<body")):
            return True

        code_patterns = [
            r'(class|def|function|import|from|public|private|protected|#include)',
            r'(\{\s*\n|\}\s*\n|\[\s*\n|\]\s*\n)',
            r'(if\s*\(|for\s*\(|while\s*\()',
            r'(<\w+>.*?</\w+>)',  # HTML/XML tags
            r'(var|let|const)\s+\w+\s*=',  # JavaScript variable declarations
            r'#\s*\w+',  # CSS ID selectors or Python comments
            r'\.\w+\s*\{',  # CSS class selectors
            r'@media|@import|@font-face'  # CSS at-rules
        ]
        return any(re.search(pattern, content) for pattern in code_patterns)

    def _is_likely_markdown(self, content: str) -> bool:
        """Check if the content is likely markdown."""
        md_patterns = [
            r'^#\s+.+$',  # Headers
            r'^\*\s+.+$',  # Unordered lists
            r'^\d+\.\s+.+$',  # Ordered lists
            r'\[.+\]\(.+\)',  # Links
            r'!\[.+\]\(.+\)'  # Images
        ]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in md_patterns)

    def _is_likely_json(self, content: str) -> bool:
        """Check if the content is likely JSON."""
        try:
            content = content.strip()
            if (content.startswith('{') and content.endswith('}')) or (
                    content.startswith('[') and content.endswith(']')):
                json.loads(content)
                return True
        except:
            pass
        return False

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be used as a filename.
        
        :param name: The string to sanitize.
        :return: A sanitized filename.
        """
        # Replace spaces with underscores
        name = name.replace(' ', '_')

        # Remove invalid characters
        name = re.sub(r'[^\w\-\.]', '', name)

        # Limit length
        if len(name) > 50:
            name = name[:50]

        return name.lower()

    def _process_file_path(self, file_path: str) -> Tuple[str, str]:
        """
        Process a file path to extract the file name and type, and create directories if needed.
        
        :param file_path: The file path to process
        :return: Tuple of (file_name, file_type)
        """
        # Get the file name and extension
        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_name)[1].lstrip('.')

        return os.path.splitext(file_name)[0], file_type
