import time
import json
import requests
import threading
from channel.wechatmp.common import *
from wechatpy.client import WeChatClient
from common.log import logger
from config import conf


class WechatMPClient(WeChatClient):
    def __init__(self, appid, secret, access_token=None,
                 session=None, timeout=None, auto_retry=True):
        super(WechatMPClient, self).__init__(
            appid, secret, access_token, session, timeout, auto_retry
        )
        self.fetch_access_token_lock = threading.Lock()

    def fetch_access_token(self):
        """
        获取 access token
        详情请参考 http://mp.weixin.qq.com/wiki/index.php?title=通用接口文档

        :return: 返回的 JSON 数据包
        """
        with self.fetch_access_token_lock:
            access_token = self.session.get(self.access_token_key)
            if access_token:
                if not self.expires_at:
                    return access_token
                timestamp = time.time()
                if self.expires_at - timestamp > 60:
                    return access_token
            return super().fetch_access_token()
        