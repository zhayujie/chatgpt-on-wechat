from typing import Any, List

from tools.base_tools import BASE_TOOLS
from tools.bot_tools import BOT_TOOLS
from tools.custom_tools import CUSTOM_TOOL
from lib.langchain_lite.chains.api import news_docs, tmdb_docs, podcast_docs
from lib.langchain_lite.chains.api.base import APIChain
from lib.langchain_lite.llms.base import BaseLLM
from tools.base_tool import BaseTool
from tools.tool import Tool


def _get_news_api(llm: BaseLLM, **kwargs: Any) -> BaseTool:
    news_api_key = kwargs["news_api_key"]
    chain = APIChain.from_llm_and_api_docs(
        llm, news_docs.NEWS_DOCS, headers={"X-Api-Key": news_api_key}
    )
    return Tool(
        name="News API",
        description="Use this when you want to get information about the top headlines of current news stories. The "
                    "input should be a question in natural language that this API can answer.",
        func=chain.run,
    )


def _get_tmdb_api(llm: BaseLLM, **kwargs: Any) -> BaseTool:
    tmdb_bearer_token = kwargs["tmdb_bearer_token"]
    chain = APIChain.from_llm_and_api_docs(
        llm,
        tmdb_docs.TMDB_DOCS,
        headers={"Authorization": f"Bearer {tmdb_bearer_token}"},
    )
    return Tool(
        name="TMDB API",
        description="Useful for when you want to get information from The Movie Database. The input should be a "
                    "question in natural language that this API can answer.",
        func=chain.run,
    )


def _get_podcast_api(llm: BaseLLM, **kwargs: Any) -> BaseTool:
    listen_api_key = kwargs["listen_api_key"]
    chain = APIChain.from_llm_and_api_docs(
        llm,
        podcast_docs.PODCAST_DOCS,
        headers={"X-ListenAPI-Key": listen_api_key},
    )
    return Tool(
        name="Podcast API",
        description="Use the Listen Notes Podcast API to search all podcasts or episodes. The input should be a "
                    "question in natural language that this API can answer.",
        func=chain.run,
    )


BOT_WITH_KEY_TOOLS = {
    "news-api": (_get_news_api, ["news_api_key"]),
    "tmdb-api": (_get_tmdb_api, ["tmdb_bearer_token"]),
    "podcast-api": (_get_podcast_api, ["listen_api_key"]),
}


CUSTOM_WITH_KEY_TOOL = {

}


def get_all_tool_names() -> List[str]:
    """Get a list of all possible tool names."""
    return (
        list(BASE_TOOLS)
        + list(BOT_TOOLS)
        + list(BOT_WITH_KEY_TOOLS)
        + list(CUSTOM_TOOL)
        + list(CUSTOM_WITH_KEY_TOOL)
        # + list(OPTIONAL_ADVANCED_TOOLS)
    )
