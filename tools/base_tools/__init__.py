from tools.base_tool import BaseTool
from tools.base_tools.python.tool import PythonREPLTool
from tools.base_tools.requests.tool import RequestsGetTool
from tools.tool import Tool
from tools.utilities.bash import BashProcess
from tools.utilities.requests import RequestsWrapper


def _get_python_repl() -> BaseTool:
    return PythonREPLTool()


def _get_requests() -> BaseTool:
    return RequestsGetTool(requests_wrapper=RequestsWrapper())


def _get_terminal() -> BaseTool:
    return Tool(
        name="Terminal",
        description="Executes commands in a terminal. Input should be valid commands, and the output will be any "
                    "output from running that command.",
        func=BashProcess().run,
    )


BASE_TOOLS = {
    "python_repl": _get_python_repl,
    "requests": _get_requests,
    "terminal": _get_terminal,
}