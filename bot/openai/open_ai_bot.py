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
        if not context or not context.get('type') or context.get('type') == 'TEXT':
            return self.reply_text(query)
        elif context.get('type', None) == 'IMAGE_CREATE':
            return self.create_img(query)

    def reply_text(self, query):
        logger.info("[OPEN_AI] query={}".format(query))
        try:
            response = openai.Completion.create(
                model="text-davinci-003",  # 对话模型的名称
                prompt=query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                max_tokens=1200,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.6,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["#"]
            )
            res_content = response.choices[0]["text"].strip()
        except Exception as e:
            logger.exception(e)
            return None
        logger.info("[OPEN_AI] reply={}".format(res_content))
        return res_content

    def create_img(self, query):
        try:
            logger.info("[OPEN_AI] image_query={}".format(query))
            response = openai.Image.create(
                prompt=query,    #图片描述
                n=1,             #每次生成图片的数量
                size="256x256"   #图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response['data'][0]['url']
            logger.info("[OPEN_AI] image_url={}".format(image_url))
        except Exception as e:
            logger.exception(e)
            return None
        return image_url

    def edit_img(self, query, src_img):
        openai.api_key = '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'
        try:
            response = openai.Image.create_edit(
                image=open(src_img, 'rb'),
                mask=open('cat-mask.png', 'rb'),
                prompt=query,
                n=1,
                size='512x512'
            )
            image_url = response['data'][0]['url']
            logger.info("[OPEN_AI] image_url={}".format(image_url))
        except Exception as e:
            logger.exception(e)
            return None
        return image_url

    def migration_img(self, query, src_img):
        openai.api_key = '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'

        try:
            response = openai.Image.create_variation(
                image=open(src_img, 'rb'),
                n=1,
                size="512x512"
            )
            image_url = response['data'][0]['url']
            logger.info("[OPEN_AI] image_url={}".format(image_url))
        except Exception as e:
            logger.exception(e)
            return None
        return image_url
