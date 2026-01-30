import platform
import subprocess
from typing import Dict, Any

from agent.tools.base_tool import BaseTool, ToolResult


class Terminal(BaseTool):
    name: str = "terminal"
    description: str = "A tool to run terminal commands on the local system"
    params: dict = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": f"The terminal command to execute which should be valid in {platform.system()} platform"
            }
        },
        "required": ["command"]
    }
    config: dict = {}

    def __init__(self, config=None):
        self.config = config or {}
        # Set of dangerous commands that should be blocked
        self.command_ban_set = {"halt", "poweroff", "shutdown", "reboot", "rm", "kill",
                                "exit", "sudo", "su", "userdel", "groupdel", "logout", "alias"}

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute a terminal command safely.

        :param args: Dictionary containing the command to execute
        :return: Result of the command execution
        """
        command = args.get("command", "").strip()

        # Check if the command is safe to execute
        if not self._is_safe_command(command):
            return ToolResult.fail(result=f"Command '{command}' is not allowed for security reasons.")

        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,  # Raise exception on non-zero return code
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.config.get("timeout", 30)
            )

            return ToolResult.success({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": command
            })
        except subprocess.CalledProcessError as e:
            # Preserve the original error handling for CalledProcessError
            return ToolResult.fail({
                "stdout": e.stdout,
                "stderr": e.stderr,
                "return_code": e.returncode,
                "command": command
            })
        except subprocess.TimeoutExpired:
            return ToolResult.fail(result=f"Command timed out after {self.config.get('timeout', 20)} seconds.")
        except Exception as e:
            return ToolResult.fail(result=f"Error executing command: {str(e)}")

    def _is_safe_command(self, command: str) -> bool:
        """
        Check if a command is safe to execute.

        :param command: The command to check
        :return: True if the command is safe, False otherwise
        """
        # Split the command to get the base command
        cmd_parts = command.split()
        if not cmd_parts:
            return False

        base_cmd = cmd_parts[0].lower()

        # Check if the base command is in the ban list
        if base_cmd in self.command_ban_set:
            return False

        # Check for sudo/su commands
        if any(banned in command.lower() for banned in ["sudo ", "su -"]):
            return False

        # Check for rm -rf or similar dangerous patterns
        if "rm" in base_cmd and ("-rf" in command or "-r" in command or "-f" in command):
            return False

        # Additional security checks can be added here

        return True
