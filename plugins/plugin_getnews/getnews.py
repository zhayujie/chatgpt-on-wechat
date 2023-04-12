# encoding:utf-8

from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
import plugins
from plugins import *
from common.log import logger
import requests
import json


@plugins.register(name="getnews", desire_priority=-1, hidden=True, desc="A simple plugin that says getnews", version="0.1", author="congxu")
class getnews(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        self.url = "https://v2.alapi.cn/api/zaobao"
        self.headers = {'Content-Type': "application/x-www-form-urlencoded"}
        self.getnews_api_token = "UDuxUGXTKAlCJ3qt"
        self.payload = "token="+getnews_api_token+"&format=json"
        logger.info("[getnews] inited")

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return
        
        content = e_context['context'].content
        logger.debug("[getnews] on_handle_context. content: %s" % content)
        if content == "news":
            reply = Reply()
            reply.type = ReplyType.TEXT
            #获取新闻
            req = requests.request("POST", url, data=payload, headers=headers)
            news_json = json.loads(req.text) 
            news_date = news_json["data"]["date"]
            news_reasult = '\n'.join(news_json["data"]["news"])

            msg:ChatMessage = e_context['context']['msg']
            if e_context['context']['isgroup']:
                reply.content = f"早上好, " + news_date +"\n" + response
            else:
                reply.content = f"早上好, " + news_date +"\n" + response
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑

        # if content == "Hi":
        #     reply = Reply()
        #     reply.type = ReplyType.TEXT
        #     reply.content = "Hi"
        #     e_context['reply'] = reply
        #     e_context.action = EventAction.BREAK  # 事件结束，进入默认处理逻辑，一般会覆写reply

        # if content == "End":
        #     # 如果是文本消息"End"，将请求转换成"IMAGE_CREATE"，并将content设置为"The World"
        #     e_context['context'].type = ContextType.IMAGE_CREATE
        #     content = "The World"
        #     e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑

    def get_help_text(self, **kwargs):
        help_text = "输入getnews，今天新闻\n"
        return help_text
