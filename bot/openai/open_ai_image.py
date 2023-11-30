import time

import openai

from common.log import logger
from common.token_bucket import TokenBucket
from config import conf

from hyaigc import Image


# OPENAI提供的画图接口
class OpenAIImage(object):
    def __init__(self):
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("rate_limit_dalle"):
            self.tb4dalle = TokenBucket(conf().get("rate_limit_dalle", 50))

    def create_img(self, query, retry_count=0, api_key=None):
        try:
            if conf().get("rate_limit_dalle") and not self.tb4dalle.get_token():
                return False, "请求太快了，请休息一下再问我吧"
            logger.info("[OPEN_AI] image_query={}".format(query))

            # response = openai.Image.create(
            #     api_key=api_key,
            #     prompt=query,  # 图片描述
            #     n=1,  # 每次生成图片的数量
            #     model=conf().get("text_to_image") or "dall-e-2",
            #     # size=conf().get("image_create_size", "256x256"),  # 图片大小,可选有 256x256, 512x512, 1024x1024
            # )
            # image_url = response["data"][0]["url"]
            # logger.info("[OPEN_AI] image_url={}".format(image_url))

            logger.info("[OPEN_AI] using huya aigc for create img")
            ai = Image(user='qatest', test=False)
            response = ai.txt2img(Image.CdnType.OpenAI, query, n=1, size=conf().get("image_create_size", "1024x1024"))
            logger.info("[OPEN_AI] hyaigc_response={}".format(response))
            image_url = response[0]
            logger.info("[OPEN_AI] hyaigc_image_url={}".format(image_url))

            if not image_url:
                raise Exception('ImgCreate failed')

            return True, image_url
        except openai.RateLimitError as e:
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.create_img(query, retry_count + 1)
            else:
                return False, "画图出现问题，请休息一下再问我吧"
        except Exception as e:
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[OPEN_AI] ImgCreate failed, 第{}次重试".format(retry_count + 1))
                return self.create_img(query, retry_count + 1)
            else:
                if "txt2img" in str(e):  # 专门针对公司hyaigc基建接口的错误处理
                    import json
                    return False, json.loads(e.args[0].replace("txt2img", "").strip())["error"]["message"]
                return False, "画图出现问题，请休息一下再问我吧"
