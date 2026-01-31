import math

from agent.tools.base_tool import BaseTool, ToolResult


class Calculator(BaseTool):
    name: str = "calculator"
    description: str = "A tool to perform basic mathematical calculations."
    params: dict = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate (e.g., '2 + 2', '5 * 3', 'sqrt(16)'). "
                               "Ensure your input is a valid Python expression, it will be evaluated directly."
            }
        },
        "required": ["expression"]
    }
    config: dict = {}

    def execute(self, args: dict) -> ToolResult:
        try:
            # Get the expression
            expression = args["expression"]

            # Create a safe local environment containing only basic math functions
            safe_locals = {
                "abs": abs,
                "round": round,
                "max": max,
                "min": min,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "pi": math.pi,
                "e": math.e,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "floor": math.floor,
                "ceil": math.ceil
            }

            # Safely evaluate the expression
            result = eval(expression, {"__builtins__": {}}, safe_locals)

            return ToolResult.success({
                "result": result,
                "expression": expression
            })
        except Exception as e:
            return ToolResult.success({
                "error": str(e),
                "expression": args.get("expression", "")
            })
