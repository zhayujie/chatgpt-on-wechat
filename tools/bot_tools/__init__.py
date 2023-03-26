from lib.langchain_lite.chains.api import open_meteo_docs
from lib.langchain_lite.chains.api.base import APIChain
from lib.langchain_lite.llms.base import BaseLLM
from tools.base_tool import BaseTool
from tools.bot_tools.llm_math import LLMMathChain
from tools.bot_tools.pal.base import PALChain
from tools.tool import Tool


def _get_pal_math(llm: BaseLLM) -> BaseTool:
    return Tool(
        name="PAL-MATH",
        description="A language model that is really good at solving complex word math problems. Input should be a "
                    "fully worded hard word math problem.",
        func=PALChain.from_math_prompt(llm).run,
    )


def _get_pal_colored_objects(llm: BaseLLM) -> BaseTool:
    return Tool(
        name="PAL-COLOR-OBJ",
        description="A language model that is really good at reasoning about position and the color attributes of "
                    "objects. Input should be a fully worded hard reasoning problem. Make sure to include all "
                    "information about the objects AND the final question you want to answer.",
        func=PALChain.from_colored_object_prompt(llm).run,
    )


def _get_llm_math(llm: BaseLLM) -> BaseTool:
    return Tool(
        name="Calculator",
        description="Useful for when you need to answer questions about math.",
        func=LLMMathChain(llm=llm, callback_manager=llm.callback_manager).run,
        coroutine=LLMMathChain(llm=llm, callback_manager=llm.callback_manager).arun,
    )


def _get_open_meteo_api(llm: BaseLLM) -> BaseTool:
    chain = APIChain.from_llm_and_api_docs(llm, open_meteo_docs.OPEN_METEO_DOCS)
    return Tool(
        name="Open Meteo API",
        description="Useful for when you want to get weather information from the OpenMeteo API. The input should be "
                    "a question in natural language that this API can answer.",
        func=chain.run,
    )


BOT_TOOLS = {
    "pal-math": _get_pal_math,
    "pal-colored-objects": _get_pal_colored_objects,
    "llm-math": _get_llm_math,
    "open-meteo-api": _get_open_meteo_api,
}
