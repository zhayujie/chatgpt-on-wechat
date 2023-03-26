"""Load bot."""
from typing import Any, Optional, Sequence

from bots.all_bot_list import BOT_TO_CLASS
from bots.bot_executor import BotExecutor
from lib.langchain_lite.callbacks import BaseCallbackManager
from lib.langchain_lite.llms.base import BaseLanguageModel
from tools.base_tool import BaseTool


def initialize_bot(
    tools: Sequence[BaseTool],
    llm: BaseLanguageModel,
    bot: Optional[str] = None,
    callback_manager: Optional[BaseCallbackManager] = None,
    bot_kwargs: Optional[dict] = None,
    **kwargs: Any,
) -> BotExecutor:
    """Load an bot executor given tools and LLM.

    Args:
        tools: List of tools this bot has access to.
        llm: Language model to use as the bot.
        bot: A string that specified the bot type to use. Valid options are:
            `qa-bot`
            `chat-bot`
            `catgirl-bot`
           If None, will default to
            `qa-bot`.
        callback_manager: CallbackManager to use. Global callback manager is used if
            not provided. Defaults to None.
        bot_kwargs: Additional key word arguments to pass to the underlying bot
        **kwargs: Additional key word arguments passed to the bot executor

    Returns:
        An bot executor
    """

    if bot not in BOT_TO_CLASS:
        raise ValueError(
            f"Got unknown bot type: {bot}. "
            f"Valid types are: {BOT_TO_CLASS.keys()}."
        )
    if bot is None:
        bot = "default"
    bot_cls = BOT_TO_CLASS[bot]

    bot_kwargs = bot_kwargs or {}
    bot_obj = bot_cls.from_llm_and_tools(
        llm, tools, callback_manager=callback_manager, **bot_kwargs
    )

    return BotExecutor.from_bot_and_tools(
        bot=bot_obj,
        tools=tools,
        callback_manager=callback_manager,
        **kwargs,
    )
