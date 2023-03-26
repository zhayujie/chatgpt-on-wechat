"""Chain that takes in an input and produces an action and action input."""
from __future__ import annotations

import json
import logging
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import yaml
from pydantic import BaseModel, root_validator

from lib.langchain_lite.callbacks import BaseCallbackManager
from lib.langchain_lite.chains import LLMChain
from lib.langchain_lite.llms.base import BaseLLM
from lib.langchain_lite.prompts import BasePromptTemplate
from lib.langchain_lite.prompts import PromptTemplate
from lib.langchain_lite.schema import BotAction, BotFinish, BaseMessage
from tools.base_tool import BaseTool

logger = logging.getLogger()


class Bot(BaseModel):
    """Class responsible for calling the language model and deciding the action.

    This is driven by an LLMChain. The prompt in the LLMChain MUST include
    a variable called "bot_scratchpad" where the bot can put its
    intermediary work.
    """

    llm_chain: LLMChain
    allowed_tools: Optional[List[str]] = None
    return_values: List[str] = ["output"]

    @abstractmethod
    def _extract_tool_and_input(self, text: str) -> Optional[Tuple[str, str]]:
        """Extract tool and tool input from llm output."""

    def _fix_text(self, text: str) -> str:
        """Fix the text."""
        raise ValueError("fix_text not implemented for this bot.")

    @property
    def _stop(self) -> List[str]:
        return [
            f"\n{self.observation_prefix.rstrip()}",
            f"\n\t{self.observation_prefix.rstrip()}",
        ]

    def _construct_scratchpad(
        self, intermediate_steps: List[Tuple[BotAction, str]]
    ) -> Union[str, List[BaseMessage]]:
        """Construct the scratchpad that lets the bot continue its thought process."""
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\n{self.observation_prefix}{observation}\n{self.llm_prefix}"
        return thoughts

    def _get_next_action(self, full_inputs: Dict[str, str]) -> BotAction:
        full_output = self.llm_chain.predict(**full_inputs)
        parsed_output = self._extract_tool_and_input(full_output)
        while parsed_output is None:
            full_output = self._fix_text(full_output)
            full_inputs["bot_scratchpad"] += full_output
            output = self.llm_chain.predict(**full_inputs)
            full_output += output
            parsed_output = self._extract_tool_and_input(full_output)
        return BotAction(
            tool=parsed_output[0], tool_input=parsed_output[1], log=full_output
        )

    def plan(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Union[BotAction, BotFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        action = self._get_next_action(full_inputs)
        if action.tool == self.finish_tool_name:
            return BotFinish({"output": action.tool_input}, action.log)
        return action

    def get_full_inputs(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """Create the full inputs for the LLMChain from intermediate steps."""
        thoughts = self._construct_scratchpad(intermediate_steps)
        new_inputs = {"bot_scratchpad": thoughts, "stop": self._stop}
        full_inputs = {**kwargs, **new_inputs}
        return full_inputs

    def prepare_for_new_call(self) -> None:
        """Prepare the bot for new call, if needed."""
        pass

    @property
    def finish_tool_name(self) -> str:
        """Name of the tool to use to finish the chain."""
        return "Final Answer"

    @property
    def input_keys(self) -> List[str]:
        """Return the input keys.

        :meta private:
        """
        return list(set(self.llm_chain.input_keys) - {"bot_scratchpad"})

    @root_validator()
    def validate_prompt(cls, values: Dict) -> Dict:
        """Validate that prompt matches format."""
        prompt = values["llm_chain"].prompt
        if "bot_scratchpad" not in prompt.input_variables:
            logger.warning(
                "`bot_scratchpad` should be a variable in prompt.input_variables."
                " Did not find it, so adding it at the end."
            )
            prompt.input_variables.append("bot_scratchpad")
            if isinstance(prompt, PromptTemplate):
                prompt.template += "\n{bot_scratchpad}"
            else:
                raise ValueError(f"Got unexpected prompt type {type(prompt)}")
        return values

    @property
    @abstractmethod
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""

    @property
    @abstractmethod
    def llm_prefix(self) -> str:
        """Prefix to append the LLM call with."""

    @classmethod
    @abstractmethod
    def create_prompt(cls, tools: Sequence[BaseTool]) -> BasePromptTemplate:
        """Create a prompt for this class."""

    @classmethod
    def _validate_tools(cls, tools: Sequence[BaseTool]) -> None:
        """Validate that appropriate tools are passed in."""
        pass

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLLM,
        tools: Sequence[BaseTool],
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ) -> Bot:
        """Construct an bot from an LLM and tools."""
        cls._validate_tools(tools)
        llm_chain = LLMChain(
            llm=llm,
            prompt=cls.create_prompt(tools),
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return cls(llm_chain=llm_chain, allowed_tools=tool_names, **kwargs)

    def return_stopped_response(
        self,
        early_stopping_method: str,
        intermediate_steps: List[Tuple[BotAction, str]],
        **kwargs: Any,
    ) -> BotFinish:
        """Return response when bot has been stopped due to max iterations."""
        if early_stopping_method == "force":
            # `force` just returns a constant string
            return BotFinish({"output": "Bot stopped due to max iterations."}, "")
        elif early_stopping_method == "generate":
            # Generate does one final forward pass
            thoughts = ""
            for action, observation in intermediate_steps:
                thoughts += action.log
                thoughts += (
                    f"\n{self.observation_prefix}{observation}\n{self.llm_prefix}"
                )
            # Adding to the previous steps, we now tell the LLM to make a final pred
            thoughts += (
                "\n\nI now need to return a final answer based on the previous steps:"
            )
            new_inputs = {"bot_scratchpad": thoughts, "stop": self._stop}
            full_inputs = {**kwargs, **new_inputs}
            full_output = self.llm_chain.predict(**full_inputs)
            # We try to extract a final answer
            parsed_output = self._extract_tool_and_input(full_output)
            if parsed_output is None:
                # If we cannot extract, we just return the full output
                return BotFinish({"output": full_output}, full_output)
            tool, tool_input = parsed_output
            if tool == self.finish_tool_name:
                # If we can extract, we send the correct stuff
                return BotFinish({"output": tool_input}, full_output)
            else:
                # If we can extract, but the tool is not the final tool,
                # we just return the full output
                return BotFinish({"output": full_output}, full_output)
        else:
            raise ValueError(
                "early_stopping_method should be one of `force` or `generate`, "
                f"got {early_stopping_method}"
            )

    @property
    @abstractmethod
    def _bot_type(self) -> str:
        """Return Identifier of bot type."""

    def dict(self, **kwargs: Any) -> Dict:
        """Return dictionary representation of bot."""
        _dict = super().dict()
        _dict["_type"] = self._bot_type
        return _dict

    def save(self, file_path: Union[Path, str]) -> None:
        """Save the bot.

        Args:
            file_path: Path to file to save the bot to.

        Example:
        .. code-block:: python

            # If working with bot executor
            bot.bot.save(file_path="path/bot.yaml")
        """
        # Convert file to Path object.
        if isinstance(file_path, str):
            save_path = Path(file_path)
        else:
            save_path = file_path

        directory_path = save_path.parent
        directory_path.mkdir(parents=True, exist_ok=True)

        # Fetch dictionary to save
        bot_dict = self.dict()

        if save_path.suffix == ".json":
            with open(file_path, "w") as f:
                json.dump(bot_dict, f, indent=4)
        elif save_path.suffix == ".yaml":
            with open(file_path, "w") as f:
                yaml.dump(bot_dict, f, default_flow_style=False)
        else:
            raise ValueError(f"{save_path} must be json or yaml")

    async def aplan(
        self, intermediate_steps: List[Tuple[BotAction, str]], **kwargs: Any
    ) -> Union[BotAction, BotFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        action = await self._aget_next_action(full_inputs)
        if action.tool == self.finish_tool_name:
            return BotFinish({"output": action.tool_input}, action.log)
        return action

    async def _aget_next_action(self, full_inputs: Dict[str, str]) -> BotAction:
        full_output = await self.llm_chain.apredict(**full_inputs)
        parsed_output = self._extract_tool_and_input(full_output)
        while parsed_output is None:
            full_output = self._fix_text(full_output)
            full_inputs["bot_scratchpad"] += full_output
            output = await self.llm_chain.apredict(**full_inputs)
            full_output += output
            parsed_output = self._extract_tool_and_input(full_output)
        return BotAction(
            tool=parsed_output[0], tool_input=parsed_output[1], log=full_output
        )
