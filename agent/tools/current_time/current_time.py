import datetime
import time

from agent.tools.base_tool import BaseTool, ToolResult


class CurrentTime(BaseTool):
    name: str = "time"
    description: str = "A tool to get current date and time information."
    params: dict = {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "Optional format for the time (e.g., 'iso', 'unix', 'human'). Default is 'human'."
            },
            "timezone": {
                "type": "string",
                "description": "Optional timezone specification (e.g., 'UTC', 'local'). Default is 'local'."
            }
        },
        "required": []
    }
    config: dict = {}

    def execute(self, args: dict) -> ToolResult:
        try:
            # Get the format and timezone parameters, with defaults
            time_format = args.get("format", "human").lower()
            timezone = args.get("timezone", "local").lower()

            # Get current time
            current_time = datetime.datetime.now()

            # Handle timezone if specified
            if timezone == "utc":
                current_time = datetime.datetime.utcnow()

            # Format the time according to the specified format
            if time_format == "iso":
                # ISO 8601 format
                formatted_time = current_time.isoformat()
            elif time_format == "unix":
                # Unix timestamp (seconds since epoch)
                formatted_time = time.time()
            else:
                # Human-readable format
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            # Prepare additional time components for the response
            year = current_time.year
            month = current_time.month
            day = current_time.day
            hour = current_time.hour
            minute = current_time.minute
            second = current_time.second
            weekday = current_time.strftime("%A")  # Full weekday name

            result = {
                "current_time": formatted_time,
                "components": {
                    "year": year,
                    "month": month,
                    "day": day,
                    "hour": hour,
                    "minute": minute,
                    "second": second,
                    "weekday": weekday
                },
                "format": time_format,
                "timezone": timezone
            }
            return ToolResult.success(result=result)
        except Exception as e:
            return ToolResult.fail(result=str(e))
