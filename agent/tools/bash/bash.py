"""
Bash tool - Execute bash commands
"""

import os
import subprocess
import tempfile
from typing import Dict, Any

from agent.tools.base_tool import BaseTool, ToolResult
from agent.tools.utils.truncate import truncate_tail, format_size, DEFAULT_MAX_LINES, DEFAULT_MAX_BYTES


class Bash(BaseTool):
    """Tool for executing bash commands"""

    name: str = "bash"
    description: str = f"""Execute a bash command in the current working directory. Returns stdout and stderr. Output is truncated to last {DEFAULT_MAX_LINES} lines or {DEFAULT_MAX_BYTES // 1024}KB (whichever is hit first). If truncated, full output is saved to a temp file.

IMPORTANT SAFETY GUIDELINES:
- You can freely create, modify, and delete files within the current workspace
- For operations outside the workspace or potentially destructive commands (rm -rf, system commands, etc.), always explain what you're about to do and ask for user confirmation first
- Be especially careful with: file deletions, system modifications, network operations, or commands that might affect system stability
- When in doubt, describe the command's purpose and ask for permission before executing"""

    params: dict = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Bash command to execute"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (optional, default: 30)"
            }
        },
        "required": ["command"]
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.cwd = self.config.get("cwd", os.getcwd())
        # Ensure working directory exists
        if not os.path.exists(self.cwd):
            os.makedirs(self.cwd, exist_ok=True)
        self.default_timeout = self.config.get("timeout", 30)
        # Enable safety mode by default (can be disabled in config)
        self.safety_mode = self.config.get("safety_mode", True)

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute a bash command
        
        :param args: Dictionary containing the command and optional timeout
        :return: Command output or error
        """
        command = args.get("command", "").strip()
        timeout = args.get("timeout", self.default_timeout)

        if not command:
            return ToolResult.fail("Error: command parameter is required")

        # Optional safety check - only warn about extremely dangerous commands
        if self.safety_mode:
            warning = self._get_safety_warning(command)
            if warning:
                return ToolResult.fail(
                    f"Safety Warning: {warning}\n\nIf you believe this command is safe and necessary, please ask the user for confirmation first, explaining what the command does and why it's needed.")

        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )

            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            # Check if we need to save full output to temp file
            temp_file_path = None
            total_bytes = len(output.encode('utf-8'))

            if total_bytes > DEFAULT_MAX_BYTES:
                # Save full output to temp file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log', prefix='bash-') as f:
                    f.write(output)
                    temp_file_path = f.name

            # Apply tail truncation
            truncation = truncate_tail(output)
            output_text = truncation.content or "(no output)"

            # Build result
            details = {}

            if truncation.truncated:
                details["truncation"] = truncation.to_dict()
                if temp_file_path:
                    details["full_output_path"] = temp_file_path

                # Build notice
                start_line = truncation.total_lines - truncation.output_lines + 1
                end_line = truncation.total_lines

                if truncation.last_line_partial:
                    # Edge case: last line alone > 30KB
                    last_line = output.split('\n')[-1] if output else ""
                    last_line_size = format_size(len(last_line.encode('utf-8')))
                    output_text += f"\n\n[Showing last {format_size(truncation.output_bytes)} of line {end_line} (line is {last_line_size}). Full output: {temp_file_path}]"
                elif truncation.truncated_by == "lines":
                    output_text += f"\n\n[Showing lines {start_line}-{end_line} of {truncation.total_lines}. Full output: {temp_file_path}]"
                else:
                    output_text += f"\n\n[Showing lines {start_line}-{end_line} of {truncation.total_lines} ({format_size(DEFAULT_MAX_BYTES)} limit). Full output: {temp_file_path}]"

            # Check exit code
            if result.returncode != 0:
                output_text += f"\n\nCommand exited with code {result.returncode}"
                return ToolResult.fail({
                    "output": output_text,
                    "exit_code": result.returncode,
                    "details": details if details else None
                })

            return ToolResult.success({
                "output": output_text,
                "exit_code": result.returncode,
                "details": details if details else None
            })

        except subprocess.TimeoutExpired:
            return ToolResult.fail(f"Error: Command timed out after {timeout} seconds")
        except Exception as e:
            return ToolResult.fail(f"Error executing command: {str(e)}")

    def _get_safety_warning(self, command: str) -> str:
        """
        Get safety warning for potentially dangerous commands
        Only warns about extremely dangerous system-level operations
        
        :param command: Command to check
        :return: Warning message if dangerous, empty string if safe
        """
        cmd_lower = command.lower().strip()

        # Only block extremely dangerous system operations
        dangerous_patterns = [
            # System shutdown/reboot
            ("shutdown", "This command will shut down the system"),
            ("reboot", "This command will reboot the system"),
            ("halt", "This command will halt the system"),
            ("poweroff", "This command will power off the system"),

            # Critical system modifications
            ("rm -rf /", "This command will delete the entire filesystem"),
            ("rm -rf /*", "This command will delete the entire filesystem"),
            ("dd if=/dev/zero", "This command can destroy disk data"),
            ("mkfs", "This command will format a filesystem, destroying all data"),
            ("fdisk", "This command modifies disk partitions"),

            # User/system management (only if targeting system users)
            ("userdel root", "This command will delete the root user"),
            ("passwd root", "This command will change the root password"),
        ]

        for pattern, warning in dangerous_patterns:
            if pattern in cmd_lower:
                return warning

        # Check for recursive deletion outside workspace
        if "rm" in cmd_lower and "-rf" in cmd_lower:
            # Allow deletion within current workspace
            if not any(path in cmd_lower for path in ["./", self.cwd.lower()]):
                # Check if targeting system directories
                system_dirs = ["/bin", "/usr", "/etc", "/var", "/home", "/root", "/sys", "/proc"]
                if any(sysdir in cmd_lower for sysdir in system_dirs):
                    return "This command will recursively delete system directories"

        return ""  # No warning needed
