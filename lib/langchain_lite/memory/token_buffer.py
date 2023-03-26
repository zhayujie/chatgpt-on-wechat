from typing import Any, Dict, List

from pydantic import BaseModel

from common.log import logger
from lib.langchain_lite.memory.chat_memory import BaseChatMemory
from lib.langchain_lite.schema import BaseLanguageModel, BaseMessage, get_buffer_string


class ConversationTokenBufferMemory(BaseChatMemory, BaseModel):
    """Buffer for storing conversation memory."""

    human_prefix: str = "Human"
    ai_prefix: str = "AI"
    llm: BaseLanguageModel
    memory_key: str = "history"
    filter_key_list: list = []
    max_token_limit: int = 2000

    @property
    def buffer(self) -> List[BaseMessage]:
        """String buffer of memory."""
        return self.chat_memory.messages

    @property
    def memory_variables(self) -> List[str]:
        """Will always return list of memory variables.

        :meta private:
        """
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return history buffer."""
        buffer: Any = self.buffer
        if self.return_messages:
            final_buffer: Any = buffer
        else:
            final_buffer = get_buffer_string(
                buffer,
                human_prefix=self.human_prefix,
                ai_prefix=self.ai_prefix,
            )
        return {self.memory_key: final_buffer}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context from this conversation to buffer. Pruned."""
        inputs = self._filter_inputs(inputs)
        super().save_context(inputs, outputs)
        # Prune buffer if it exceeds max token limit
        buffer = self.chat_memory.messages
        curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)
        if curr_buffer_length > self.max_token_limit:
            pruned_memory = []
            while curr_buffer_length > self.max_token_limit:
                pruned_memory.append(buffer.pop(0))
                curr_buffer_length = self.llm.get_num_tokens_from_messages(buffer)

    def _filter_inputs(self, inputs: Dict[str, Any]):
        _inputs = inputs.copy()
        if not self.filter_key_list:
            logger.debug("[MEMORY]: filter_key_list is null")
            return _inputs

        for key in inputs.keys():
            if key in self.filter_key_list:
                _inputs.pop(key)
        return _inputs
