import time

import openai
import openai.error
from bridge.reply import Reply, ReplyType

from common.log import logger
from common.token_bucket import TokenBucket
from config import conf


# OPENAI提供的画图接口
class OpenAIImage(object):
    def __init__(self):
        openai.api_base = conf().get("open_ai_api_base")
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("rate_limit_dalle"):
            self.tb4dalle = TokenBucket(conf().get("rate_limit_dalle", 50))

    def create_img(self, query, retry_count=0, api_key=None, context=None):
        """
        参数：
        - context: 如果想要发送dalle3的revised_prompt，需要填写此参数
        """
        try:
            if conf().get("rate_limit_dalle") and not self.tb4dalle.get_token():
                return False, "请求太快了，请休息一下再问我吧"
            logger.info("[OPEN_AI] image_query={}".format(query))
            response = openai.Image.create(
                api_key=api_key,
                prompt=query,  # 图片描述
                n=1,  # 每次生成图片的数量
                model=conf().get("text_to_image") or "dall-e-2",
                # size=conf().get("image_create_size", "256x256"),  # 图片大小,可选有 256x256, 512x512, 1024x1024
            )
            self.send_revised_prompt(context, response["data"][0].get("revised_prompt", ""), query)
            image_url = response["data"][0]["url"]
            logger.info("[OPEN_AI] image_url={}".format(image_url))
            return True, image_url
        except openai.error.RateLimitError as e:
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.create_img(query, retry_count + 1, context=context)
            else:
                return False, "画图出现问题，请休息一下再问我吧"
        except Exception as e:
            logger.exception(e)
            return False, "画图出现问题，请休息一下再问我吧"

    def send_revised_prompt(self, context, revised_prompt, query):
        if not context or not revised_prompt:
            return
        try:
            channel = context.get("channel")
            reply = Reply(ReplyType.TEXT, f"revised_prompt:\n{revised_prompt}\n\n- - - - - - - - - - - -\n🎨 Dall-E画图：{query}")
            channel.send(reply, context)
        except Exception as e:
            logger.error(e)