# -*- coding: utf-8 -*-
import json
import threading
import time

import requests
import web

from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel.wechatmp.common import *
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from config import conf

# If using SSL, uncomment the following lines, and modify the certificate path.
# from cheroot.server import HTTPServer
# from cheroot.ssl.builtin import BuiltinSSLAdapter
# HTTPServer.ssl_adapter = BuiltinSSLAdapter(
#         certificate='/ssl/cert.pem',
#         private_key='/ssl/cert.key')


@singleton
class WechatMPChannel(ChatChannel):
    def __init__(self, passive_reply=True):
        super().__init__()
        self.passive_reply = passive_reply
        self.running = set()
        self.received_msgs = ExpiredDict(60 * 60 * 24)
        if self.passive_reply:
            self.NOT_SUPPORT_REPLYTYPE = [ReplyType.IMAGE, ReplyType.VOICE]
            self.cache_dict = dict()
            self.query1 = dict()
            self.query2 = dict()
            self.query3 = dict()
        else:
            # TODO support image
            self.NOT_SUPPORT_REPLYTYPE = [ReplyType.IMAGE, ReplyType.VOICE]
            self.app_id = conf().get("wechatmp_app_id")
            self.app_secret = conf().get("wechatmp_app_secret")
            self.access_token = None
            self.access_token_expires_time = 0
            self.access_token_lock = threading.Lock()
            self.get_access_token()

    def startup(self):
        if self.passive_reply:
            urls = ("/wx", "channel.wechatmp.SubscribeAccount.Query")
        else:
            urls = ("/wx", "channel.wechatmp.ServiceAccount.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("wechatmp_port", 8080)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def wechatmp_request(self, method, url, **kwargs):
        r = requests.request(method=method, url=url, **kwargs)
        r.raise_for_status()
        r.encoding = "utf-8"
        ret = r.json()
        if "errcode" in ret and ret["errcode"] != 0:
            raise WeChatAPIException("{}".format(ret))
        return ret

    def get_access_token(self):
        # return the access_token
        if self.access_token:
            if self.access_token_expires_time - time.time() > 60:
                return self.access_token

        # Get new access_token
        # Do not request access_token in parallel! Only the last obtained is valid.
        if self.access_token_lock.acquire(blocking=False):
            # Wait for other threads that have previously obtained access_token to complete the request
            # This happens every 2 hours, so it doesn't affect the experience very much
            time.sleep(1)
            self.access_token = None
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            }
            data = self.wechatmp_request(method="get", url=url, params=params)
            self.access_token = data["access_token"]
            self.access_token_expires_time = int(time.time()) + data["expires_in"]
            logger.info("[wechatmp] access_token: {}".format(self.access_token))
            self.access_token_lock.release()
        else:
            # Wait for token update
            while self.access_token_lock.locked():
                time.sleep(0.1)
        return self.access_token

    def send(self, reply: Reply, context: Context):
        if self.passive_reply:
            receiver = context["receiver"]
            self.cache_dict[receiver] = reply.content
            logger.info("[send] reply to {} saved to cache: {}".format(receiver, reply))
        else:
            receiver = context["receiver"]
            reply_text = reply.content
            url = "https://api.weixin.qq.com/cgi-bin/message/custom/send"
            params = {"access_token": self.get_access_token()}
            json_data = {
                "touser": receiver,
                "msgtype": "text",
                "text": {"content": reply_text},
            }
            self.wechatmp_request(
                method="post",
                url=url,
                params=params,
                data=json.dumps(json_data, ensure_ascii=False).encode("utf8"),
            )
            logger.info("[send] Do send to {}: {}".format(receiver, reply_text))
        return

    def _success_callback(self, session_id, context, **kwargs):  # 线程异常结束时的回调函数
        logger.debug(
            "[wechatmp] Success to generate reply, msgId={}".format(
                context["msg"].msg_id
            )
        )
        if self.passive_reply:
            self.running.remove(session_id)

    def _fail_callback(self, session_id, exception, context, **kwargs):  # 线程异常结束时的回调函数
        logger.exception(
            "[wechatmp] Fail to generate reply to user, msgId={}, exception={}".format(
                context["msg"].msg_id, exception
            )
        )
        if self.passive_reply:
            assert session_id not in self.cache_dict
            self.running.remove(session_id)
