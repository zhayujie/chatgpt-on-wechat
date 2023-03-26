import logging

from apps.app import App
from common.log import logger
from config import conf, load_config
from lib.langchain_lite.chains import LLMChain
from lib.langchain_lite.models.chatgpt import ChatOpenAI
from lib.langchain_lite.prompts import PromptTemplate


class LiteApp(App):

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
            self.llm = ChatOpenAI(temperature=0.9, **model_kwargs)

            self.prompt = PromptTemplate(
                input_variables=["question"],
                template="{question}?",
            )

            self.init_flag = True

    def create(self, use_tools: list):
        assert len(use_tools) == 0

        self.agent = LLMChain(llm=self.llm, prompt=self.prompt)

    def inference(self, query: str, session: list = None, retry_num: int = 0) -> str:
        assert self.agent is not None
        assert session is None
        if not query:
            logger.warn("[APP]: query is zero value")
            return ""

        try:
            response = self.agent.run(query)
            logger.info(f"[APP] response: {str(response)}")
            return str(response)
        except ValueError as e:
            logger.exception(e)
            logger.error(f"[APP] catch a ValueError: {str(e)}")
            if retry_num < 1:
                return self.inference(query, session, retry_num + 1)


if __name__ == "__main__":
    load_config()
    logger.setLevel(logging.DEBUG)

    bot = LiteApp()
    bot.create([])
    response = bot.inference("最近中国的新闻有哪些")
    print(str(response))
