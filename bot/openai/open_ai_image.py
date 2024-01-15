
import time
import requests
import json
from common.log import logger
from common.token_bucket import TokenBucket
from config import conf, get_random_key, remove_invalid_key
class OpenAIImage(object):
    def __init__(self):
        # self.api_key = get_random_key()
        self.max_retry_count = 10  # 设置最大重试次数

        if conf().get("rate_limit_dalle"):
            self.tb4dalle = TokenBucket(conf().get("rate_limit_dalle", 60))

    def create_img(self, query, retry_count=0):
        api_key = get_random_key()
        try:
            if conf().get("rate_limit_dalle") and not self.tb4dalle.get_token():
                return False, "请求太快了，请休息一下再问我吧"

            if retry_count >= self.max_retry_count:  # 检查是否超过最大重试次数
                return False, "已达到最大重试次数，请稍后再试"

            logger.info("[OPEN_AI] image_query={}".format(query))
            headers = {'Authorization': f'Bearer {api_key}'}
            data = {
                "prompt": query,
                "n": 1,
                "model": conf().get("text_to_image") or "dall-e-2",
            }
            proxy = conf().get("proxy") + '/v1/images/generations'
            response = requests.post(proxy, headers=headers, json=data)
            response.raise_for_status()
            image_url = response.json()["data"][0]["url"]
            logger.info("[OPEN_AI] image_url={}".format(image_url))
            return True, image_url
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                return False, "富强 民主 文明 和谐\n自由 平等 公正 法治\n爱国 敬业 诚信 友善"
            elif e.response.status_code == 401:
                remove_invalid_key(api_key)
                return self.create_img(query, retry_count + 1)
                # return False, "key无效，画图失败，请重试"
            elif e.response.status_code == 429:
                if retry_count < 1:
                    time.sleep(2)
                    logger.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count + 1))
                    return self.create_img(query, retry_count + 1)
                elif not (e.response.status_code == 429 and response.json().get('error', {}).get('code') == 'rate_limit_exceeded'):
                    remove_invalid_key(api_key)
                    return False, "key无效，画图失败，请重试"
                else:
                    time.sleep(10)
                    return self.create_img(query, retry_count + 1)
            else:
                if retry_count < self.max_retry_count:  # 检查是否超过最大重试次数
                    logger.exception(e)
                    remove_invalid_key(api_key)
                    time.sleep(10)
                    return self.create_img(query, retry_count + 1)
                else:
                    return False, "已达到最大重试次数，请稍后再试"
        except Exception as e:
            if retry_count < self.max_retry_count:  # 检查是否超过最大重试次数
                remove_invalid_key(api_key)
                time.sleep(10)
                logger.exception(e)
                return self.create_img(query, retry_count + 1)
            else:
                return False, "已达到最大重试次数，请稍后再试"

