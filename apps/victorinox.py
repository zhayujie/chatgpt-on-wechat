import logging

from apps.app import App
from bots.initialize import initialize_bot
from common.log import logger
from config import conf, load_config
from lib.langchain_lite.memory import ConversationTokenBufferMemory
from lib.langchain_lite.models.chatgpt import ChatOpenAI
from tools.load_tools import load_tools


class Victorinox(App):
    def __init__(self):
        super().__init__()
        if not self.init_flag:
            model_kwargs = {
                "openai_api_key": conf().get('open_ai_api_key'),
                "proxy": conf().get('proxy'),
                "model_name": "gpt-3.5-turbo",  # 对话模型的名称
                "top_p": 1,
                "frequency_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "request_timeout": 12,
                "max_retries": 3
            }
            self.llm = ChatOpenAI(temperature=0, **model_kwargs)

            self.memory = ConversationTokenBufferMemory(llm=self.llm, memory_key="chat_history",
                                                        output_key='output', max_token_limit=1000)
            self.init_flag = True

    def create(self, use_tools: list):
        logger.debug(f"Initializing {self.get_class_name()}, use_tools={use_tools}")

        if not self._check_mandatory_tools(use_tools):
            raise ValueError("_check_mandatory_tools failed")

        # loading tools from config.
        tools_kwargs = dict()
        for key, value in conf().get('app', {}).get('tools_kwargs', {}).items():
            tools_kwargs[key] = value
        tools = load_tools(use_tools, llm=self.llm, **tools_kwargs)

        # create agents
        self.agent = initialize_bot(tools, self.llm, bot="chat-bot", verbose=True,
                                    memory=self.memory, max_iterations=2, early_stopping_method="generate")

    def inference(self, query: str, session: list = None, retry_num: int = 0) -> str:
        assert self.agent is not None
        if not query:
            logger.warn("[APP]: query is zero value")
            return "query is empty"

        try:
            return self.agent.run(query)
        except ValueError as e:
            logger.exception(e)
            logger.error(f"[APP] catch a ValueError: {str(e)}")
            if retry_num < 1:
                return self.inference(query, session, retry_num+1)
            else:
                return "exceed retry_num"

    def _check_mandatory_tools(self, use_tools: list) -> bool:
        for tool in self.mandatory_tools:
            if tool not in use_tools:
                logger.error(f"You have to load {tool} as a basic tool for f{self.get_class_name()}")
                return False
        return True


if __name__ == "__main__":
    load_config()
    logger.setLevel(logging.DEBUG)

    tools_list = ["python_repl", "requests", "terminal", "pal-math", "pal-colored-objects", "llm-math", "open-meteo-api"]
    bot = Victorinox()
    bot.create(tools_list)
    # bot.inference("https://www.36kr.com/p/2186160784654466 总结这个链接的内容")
    bot.inference("姚明的身高的厘米数的3次方是多少？")
