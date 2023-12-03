# -*- coding: utf-8 -*-
"""
Author: chazzjimel
Email: chazzjimel@gmail.com
wechat：cheung-z-x

Description:
ali voice service

"""
import json
import os
import re
import time

from bridge.reply import Reply, ReplyType
from common.log import logger
from voice.voice import Voice
from voice.ali.ali_api import AliyunTokenGenerator
from voice.ali.ali_api import text_to_speech_aliyun


def textContainsEmoji(text):
    # 此正则表达式匹配大多数表情符号和特殊字符
    pattern = re.compile(
        '[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U00002600-\U000026FF]')
    return bool(pattern.search(text))


class AliVoice(Voice):
    def __init__(self):
        try:
            curdir = os.path.dirname(__file__)
            config_path = os.path.join(curdir, "config.json")
            with open(config_path, "r") as fr:
                config = json.load(fr)
            self.token = None
            self.token_expire_time = 0
            self.api_url = config.get("api_url")
            self.appkey = config.get("appkey")
            self.access_key_id = config.get("access_key_id")
            self.access_key_secret = config.get("access_key_secret")
        except Exception as e:
            logger.warn("AliVoice init failed: %s, ignore " % e)

    # def voiceToText(self, voice_file):
    #     pass

    def textToVoice(self, text):
        text = re.sub(r'[^\u4e00-\u9fa5\u3040-\u30FF\uAC00-\uD7AFa-zA-Z0-9'
                      r'äöüÄÖÜáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙâêîôûÂÊÎÔÛçÇñÑ，。！？,.]', '', text)
        # 提取 token_id 值
        token_id = self.get_valid_token()
        fileName = text_to_speech_aliyun(self.api_url, text, self.appkey, token_id)
        if fileName:
            logger.info("[Ali] textToVoice text={} voice file name={}".format(text, fileName))
            reply = Reply(ReplyType.VOICE, fileName)
        else:
            reply = Reply(ReplyType.ERROR, "抱歉，语音合成失败")
        return reply

    def get_valid_token(self):
        current_time = time.time()
        if self.token is None or current_time >= self.token_expire_time:
            get_token = AliyunTokenGenerator(self.access_key_id, self.access_key_secret)
            token_str = get_token.get_token()
            token_data = json.loads(token_str)
            self.token = token_data["Token"]["Id"]
            # 将过期时间减少一小段时间（例如5分钟），以避免在边界条件下的过期
            self.token_expire_time = token_data["Token"]["ExpireTime"] - 300
            logger.debug(f"新获取的阿里云token：{self.token}")
        else:
            logger.debug("使用缓存的token")
        return self.token