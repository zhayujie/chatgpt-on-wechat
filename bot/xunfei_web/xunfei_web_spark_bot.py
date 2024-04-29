# encoding:utf-8

import requests, json
from bot.bot import Bot
from bot.session_manager import SessionManager
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from common import const
import time
import _thread as thread
import datetime
from datetime import datetime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode
import base64
import ssl
import hashlib
import hmac
import json
from time import mktime
from urllib.parse import urlparse
import websocket
import queue
import threading
import random
from sparkdesk_web.core import SparkWeb
from pyhandytools.file import FileUtils



    # single chat
    # print(sparkWeb.chat("repeat: hello world"))

    # stream input chat
    # sparkWeb.chat_stream(history=True)

    # continue chat
    chat = sparkWeb.create_continuous_chat()
    while True:
        chat.chat(input("Ask: "))

# 消息队列 map
queue_map = dict()

# 响应队列 map
reply_map = dict()


class XunFeiWebBot(Bot):
    def __init__(self):
        super().__init__()
        sparkWeb = SparkWeb(
            self.web_cookie = conf().get("xunfei_web_cookie")
            self.web_fd = conf().get("xunfei_web_fd")
            self.web_gttoken = conf().get("xunfei_web_gttoken")
        )
        # 和wenxin使用相同的session机制
        self.sessions = SessionManager(BaiduWenxinSession, model=const.XUNFEI)

    def reply(self, query, context: Context = None) -> Reply:
        if context.type == ContextType.TEXT:
            logger.info("[XunFei] query={}".format(query))
            session_id = context["session_id"]
            request_id = self.gen_request_id(session_id)
            reply_map[request_id] = ""
            session = self.sessions.session_query(query, session_id)
            threading.Thread(target=self.create_web_socket,
                             args=(session.messages, request_id)).start()
            depth = 0
            time.sleep(0.1)
            t1 = time.time()
            usage = {}
            while depth <= 300:
                try:
                    data_queue = queue_map.get(request_id)
                    if not data_queue:
                        depth += 1
                        time.sleep(0.1)
                        continue
                    data_item = data_queue.get(block=True, timeout=0.1)
                    if data_item.is_end:
                        # 请求结束
                        del queue_map[request_id]
                        if data_item.reply:
                            reply_map[request_id] += data_item.reply
                        usage = data_item.usage
                        break

                    reply_map[request_id] += data_item.reply
                    depth += 1
                except Exception as e:
                    depth += 1
                    continue
            t2 = time.time()
            logger.info(
                f"[XunFei-API] response={reply_map[request_id]}, time={t2 - t1}s, usage={usage}"
            )
            self.sessions.session_reply(reply_map[request_id], session_id,
                                        usage.get("total_tokens"))
            reply = Reply(ReplyType.TEXT, reply_map[request_id])
            del reply_map[request_id]
            return reply
        else:
            reply = Reply(ReplyType.ERROR,
                          "Bot不支持处理{}类型的消息".format(context.type))
            return reply


    def gen_request_id(self, session_id: str):
        return session_id + "_" + str(int(time.time())) + "" + str(
            random.randint(0, 100))



   


class ReplyItem:
    def __init__(self, reply, usage=None, is_end=False):
        self.is_end = is_end
        self.reply = reply
        self.usage = usage



def run(ws, *args):
    data = json.dumps(
        gen_params(appid=ws.appid,
                   domain=ws.domain,
                   question=ws.question,
                   temperature=ws.temperature))
    ws.send(data)