import requests

from agent.tools.base_tool import BaseTool, ToolResult


class GoogleSearch(BaseTool):
    name: str = "google_search"
    description: str = "A tool to perform Google searches using the Serper API."
    params: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to perform."
            }
        },
        "required": ["query"]
    }
    config: dict = {}

    def __init__(self, config=None):
        self.config = config or {}

    def execute(self, args: dict) -> ToolResult:
        api_key = self.config.get("api_key")  # Replace with your actual API key
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "q": args.get("query"),
            "k": 10
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("statusCode") and result.get("statusCode") == 503:
            return ToolResult.fail(result=result)
        else:
            # Check if the returned result contains the 'organic' key and ensure it is a list
            if 'organic' in result and isinstance(result.get('organic'), list):
                result_data = result['organic']
            else:
                # If there are no organic results, return the full response or an empty list
                result_data = result.get('organic', []) if isinstance(result.get('organic'), list) else []
            return ToolResult.success(result=result_data)
