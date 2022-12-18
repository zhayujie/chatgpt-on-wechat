# encoding:utf-8

from bot.bot import Bot
from config import conf
from common.log import logger
import openai


# OpenAI对话模型API (可用)
class OpenAIBot(Bot):
    def __init__(self):
        openai.api_key = conf().get('open_ai_api_key')

    def reply(self, query, context=None):
        logger.info("[OPEN_AI] query={}".format(query))
        try:
            response = openai.Completion.create(
                model="text-davinci-003",      #对话模型的名称
                prompt=query,
                temperature=0.9,               #值在[0,1]之间，越大表示回复越具有不确定性
                max_tokens=1200,               #回复最大的字符数
                top_p=1,
                frequency_penalty=0.0,         #[-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.6,          #[-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["#"]
            )
            res_content = response.choices[0]["text"].strip()
        except Exception as e:
            logger.error(e)
            return None
        logger.info("[OPEN_AI] reply={}".format(res_content))
        return res_content


