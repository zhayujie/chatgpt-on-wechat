"""Functionality for loading chains."""
import json
from pathlib import Path
from typing import Any, Union

import yaml

from lib.langchain_lite.chains.api.base import APIChain
from lib.langchain_lite.chains.base import Chain
from lib.langchain_lite.chains.llm import LLMChain
from lib.langchain_lite.llms.loading import load_llm, load_llm_from_config
from lib.langchain_lite.prompts.loading import load_prompt, load_prompt_from_config
from tools.bot_tools.llm_math import LLMMathChain
from tools.bot_tools.pal.base import PALChain
from tools.utilities.loading import try_load_from_hub

URL_BASE = "https://raw.githubusercontent.com/hwchase17/lib-hub/master/chains/"


def _load_llm_chain(config: dict, **kwargs: Any) -> LLMChain:
    """Load LLM chain from config dict."""
    if "llm" in config:
        llm_config = config.pop("llm")
        llm = load_llm_from_config(llm_config)
    elif "llm_path" in config:
        llm = load_llm(config.pop("llm_path"))
    else:
        raise ValueError("One of `llm` or `llm_path` must be present.")

    if "prompt" in config:
        prompt_config = config.pop("prompt")
        prompt = load_prompt_from_config(prompt_config)
    elif "prompt_path" in config:
        prompt = load_prompt(config.pop("prompt_path"))
    else:
        raise ValueError("One of `prompt` or `prompt_path` must be present.")

    return LLMChain(llm=llm, prompt=prompt, **config)


def _load_llm_math_chain(config: dict, **kwargs: Any) -> LLMMathChain:
    if "llm" in config:
        llm_config = config.pop("llm")
        llm = load_llm_from_config(llm_config)
    elif "llm_path" in config:
        llm = load_llm(config.pop("llm_path"))
    else:
        raise ValueError("One of `llm` or `llm_path` must be present.")
    if "prompt" in config:
        prompt_config = config.pop("prompt")
        prompt = load_prompt_from_config(prompt_config)
    elif "prompt_path" in config:
        prompt = load_prompt(config.pop("prompt_path"))
    return LLMMathChain(llm=llm, prompt=prompt, **config)


def _load_pal_chain(config: dict, **kwargs: Any) -> PALChain:
    if "llm" in config:
        llm_config = config.pop("llm")
        llm = load_llm_from_config(llm_config)
    elif "llm_path" in config:
        llm = load_llm(config.pop("llm_path"))
    else:
        raise ValueError("One of `llm` or `llm_path` must be present.")
    if "prompt" in config:
        prompt_config = config.pop("prompt")
        prompt = load_prompt_from_config(prompt_config)
    elif "prompt_path" in config:
        prompt = load_prompt(config.pop("prompt_path"))
    else:
        raise ValueError("One of `prompt` or `prompt_path` must be present.")
    return PALChain(llm=llm, prompt=prompt, **config)


def _load_api_chain(config: dict, **kwargs: Any) -> APIChain:
    if "api_request_chain" in config:
        api_request_chain_config = config.pop("api_request_chain")
        api_request_chain = load_chain_from_config(api_request_chain_config)
    elif "api_request_chain_path" in config:
        api_request_chain = load_chain(config.pop("api_request_chain_path"))
    else:
        raise ValueError(
            "One of `api_request_chain` or `api_request_chain_path` must be present."
        )
    if "api_answer_chain" in config:
        api_answer_chain_config = config.pop("api_answer_chain")
        api_answer_chain = load_chain_from_config(api_answer_chain_config)
    elif "api_answer_chain_path" in config:
        api_answer_chain = load_chain(config.pop("api_answer_chain_path"))
    else:
        raise ValueError(
            "One of `api_answer_chain` or `api_answer_chain_path` must be present."
        )
    if "requests_wrapper" in kwargs:
        requests_wrapper = kwargs.pop("requests_wrapper")
    else:
        raise ValueError("`requests_wrapper` must be present.")
    return APIChain(
        api_request_chain=api_request_chain,
        api_answer_chain=api_answer_chain,
        requests_wrapper=requests_wrapper,
        **config,
    )


type_to_loader_dict = {
    "api_chain": _load_api_chain,
    "llm_chain": _load_llm_chain,
    "llm_math_chain": _load_llm_math_chain,
    "pal_chain": _load_pal_chain,
}


def load_chain_from_config(config: dict, **kwargs: Any) -> Chain:
    """Load chain from Config Dict."""
    if "_type" not in config:
        raise ValueError("Must specify a chain Type in config")
    config_type = config.pop("_type")

    if config_type not in type_to_loader_dict:
        raise ValueError(f"Loading {config_type} chain not supported")

    chain_loader = type_to_loader_dict[config_type]
    return chain_loader(config, **kwargs)


def load_chain(path: Union[str, Path], **kwargs: Any) -> Chain:
    """Unified method for loading a chain from LangChainHub or local fs."""
    if hub_result := try_load_from_hub(
        path, _load_chain_from_file, "chains", {"json", "yaml"}, **kwargs
    ):
        return hub_result
    else:
        return _load_chain_from_file(path, **kwargs)


def _load_chain_from_file(file: Union[str, Path], **kwargs: Any) -> Chain:
    """Load chain from file."""
    # Convert file to Path object.
    if isinstance(file, str):
        file_path = Path(file)
    else:
        file_path = file
    # Load from either json or yaml.
    if file_path.suffix == ".json":
        with open(file_path) as f:
            config = json.load(f)
    elif file_path.suffix == ".yaml":
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
    else:
        raise ValueError("File type must be json or yaml")

    # Override default 'verbose' and 'memory' for the chain
    if "verbose" in kwargs:
        config["verbose"] = kwargs.pop("verbose")
    if "memory" in kwargs:
        config["memory"] = kwargs.pop("memory")

    # Load the chain from the config now.
    return load_chain_from_config(config, **kwargs)
