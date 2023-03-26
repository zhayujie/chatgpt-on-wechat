"""Load tools."""
from typing import Optional

from lib.langchain_lite.callbacks import BaseCallbackManager
from lib.langchain_lite.llms.base import BaseLanguageModel
from tools.all_tool_list import *


def load_tools(
    tool_names: List[str],
    llm: Optional[BaseLanguageModel] = None,
    callback_manager: Optional[BaseCallbackManager] = None,
    **kwargs: Any,
) -> List[BaseTool]:
    """Load tools based on their name.

    Args:
        tool_names: name of tools to load.
        llm: Optional language model, may be needed to initialize certain tools.
        callback_manager: Optional callback manager. If not provided, default global callback manager will be used.

    Returns:
        List of tools.
    """
    tools = []
    for name in tool_names:
        if name in BASE_TOOLS:
            tools.append(BASE_TOOLS[name]())
        elif name in BOT_TOOLS:
            if llm is None:
                raise ValueError(f"Tool {name} requires an LLM to be provided")
            tool = BOT_TOOLS[name](llm)
            if callback_manager is not None:
                tool.callback_manager = callback_manager
            tools.append(tool)
        elif name in BOT_WITH_KEY_TOOLS:
            if llm is None:
                raise ValueError(f"Tool {name} requires an LLM to be provided")
            _get_llm_tool_func, extra_keys = BOT_WITH_KEY_TOOLS[name]
            missing_keys = set(extra_keys).difference(kwargs)
            if missing_keys:
                raise ValueError(
                    f"Tool {name} requires some parameters that were not "
                    f"provided: {missing_keys}"
                )
            sub_kwargs = {k: kwargs[k] for k in extra_keys}
            tool = _get_llm_tool_func(llm=llm, **sub_kwargs)
            if callback_manager is not None:
                tool.callback_manager = callback_manager
            tools.append(tool)
        # elif name in OPTIONAL_ADVANCED_TOOLS:
        #     _get_tool_func, extra_keys = OPTIONAL_ADVANCED_TOOLS[name]
        #     sub_kwargs = {k: kwargs[k] for k in extra_keys if k in kwargs}
        #     tool = _get_tool_func(**sub_kwargs)
        #     if callback_manager is not None:
        #         tool.callback_manager = callback_manager
        #     tools.append(tool)
        elif name in CUSTOM_TOOL:
            tools.append(CUSTOM_TOOL[name]())
        else:
            raise ValueError(f"Got unknown tool {name}")
    return tools
