"""Wrappers on top of large language models APIs."""
from typing import Dict, Type

from lib.langchain_lite.llms.openai import OpenAI, OpenAIChat
from lib.langchain_lite.llms.base import BaseLLM


__all__ = [
    "OpenAI",
    "OpenAIChat",
]

type_to_cls_dict: Dict[str, Type[BaseLLM]] = {
    "openai": OpenAI,
}
