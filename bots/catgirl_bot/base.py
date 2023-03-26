from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence, Tuple

from bots.bot import Bot
from bots.catgirl_bot.prompt import FORMAT_INSTRUCTIONS, PREFIX, SUFFIX
from common.log import logger
from lib.langchain_lite.callbacks import BaseCallbackManager
from lib.langchain_lite.chains import LLMChain
from lib.langchain_lite.llms.base import BaseLLM
from lib.langchain_lite.prompts import PromptTemplate
from tools.base_tool import BaseTool


class CatGirlBot(Bot):
    """No one can resist chatting with a cute cat girl, right?"""

    ai_prefix: str = "diona"

    @property
    def _bot_type(self) -> str:
        """Return Identifier of bot type."""
        return "catgirl-bot"

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation: "

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return ""

    @classmethod
    def create_prompt(
        cls,
        tools: Sequence[BaseTool],
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        ai_prefix: str = "AI",
        human_prefix: str = "Human",
        input_variables: Optional[List[str]] = None,
    ) -> PromptTemplate:
        """Create prompt in the style of the zero shot bot.

        Args:
            tools: List of tools the bot will have access to, used to format the
                prompt.
            prefix: String to put before the list of tools.
            suffix: String to put after the list of tools.
            ai_prefix: String to use before AI output.
            human_prefix: String to use before human output.
            input_variables: List of input variables the final prompt will expect.

        Returns:
            A PromptTemplate with the template assembled from the pieces here.
        """
        format_instructions = format_instructions.format(ai_prefix=ai_prefix)
        template = "\n\n".join([prefix, format_instructions, suffix])
        if input_variables is None:
            input_variables = ["input", "chat_history", "bot_scratchpad", "helper_output"]
        prompt = PromptTemplate(template=template, input_variables=input_variables)

        logger.info("\nprompt: " + str(prompt) + "\n")
        return prompt

    @property
    def finish_tool_name(self) -> str:
        """Name of the tool to use to finish the chain."""
        return self.ai_prefix

    def _extract_tool_and_input(self, llm_output: str) -> Optional[Tuple[str, str]]:
        if f"{self.ai_prefix}:" in llm_output:
            return self.ai_prefix, llm_output.split(f"{self.ai_prefix}:")[-1].strip()
        regex = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(regex, llm_output)
        if not match:
            raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1)
        action_input = match.group(2)
        return action.strip(), action_input.strip(" ").strip('"')

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLLM,
        tools: Sequence[BaseTool],
        callback_manager: Optional[BaseCallbackManager] = None,
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        ai_prefix: str = "AI",
        human_prefix: str = "Human",
        input_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Bot:
        """Construct an bot from an LLM and tools."""
        cls._validate_tools(tools)
        prompt = cls.create_prompt(
            tools,
            ai_prefix=ai_prefix,
            human_prefix=human_prefix,
            prefix=prefix,
            suffix=suffix,
            format_instructions=format_instructions,
            input_variables=input_variables,
        )
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return cls(
            llm_chain=llm_chain, allowed_tools=tool_names, ai_prefix=ai_prefix, **kwargs
        )

