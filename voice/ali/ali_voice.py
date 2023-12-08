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
from config import conf


class AliVoice(Voice):
    def __init__(self):
        """
        初始化AliVoice类，从配置文件加载必要的配置。
        """
        try:
            curdir = os.path.dirname(__file__)
            config_path = os.path.join(curdir, "config.json")
            with open(config_path, "r") as fr:
                config = json.load(fr)
            self.token = None
            self.token_expire_time = 0
            # 默认复用阿里云千问的 access_key 和 access_secret
            self.api_url = config.get("api_url")
            self.app_key = config.get("app_key")
            self.access_key_id = conf().get("qwen_access_key_id") or config.get("access_key_id")
            self.access_key_secret = conf().get("qwen_access_key_secret") or config.get("access_key_secret")
        except Exception as e:
            logger.warn("AliVoice init failed: %s, ignore " % e)

    def textToVoice(self, text):
        """
        将文本转换为语音文件。

        :param text: 要转换的文本。
        :return: 返回一个Reply对象，其中包含转换得到的语音文件或错误信息。
        """
        # 清除文本中的非中文、非英文和非基本字符
        text = re.sub(r'[^\u4e00-\u9fa5\u3040-\u30FF\uAC00-\uD7AFa-zA-Z0-9'
                      r'äöüÄÖÜáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙâêîôûÂÊÎÔÛçÇñÑ，。！？,.]', '', text)
        # 提取有效的token
        token_id = self.get_valid_token()
        fileName = text_to_speech_aliyun(self.api_url, text, self.app_key, token_id)
        if fileName:
            logger.info("[Ali] textToVoice text={} voice file name={}".format(text, fileName))
            reply = Reply(ReplyType.VOICE, fileName)
        else:
            reply = Reply(ReplyType.ERROR, "抱歉，语音合成失败")
        return reply

    def get_valid_token(self):
        """
        获取有效的阿里云token。

        :return: 返回有效的token字符串。
        """
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
