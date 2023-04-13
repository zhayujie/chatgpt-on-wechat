# encoding:utf-8

from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
import plugins
from plugins import *
from common.log import logger
import requests
import json
import re
from datetime import datetime


@plugins.register(name="getnews", desire_priority=-1, hidden=True, desc="A simple plugin that says getnews", version="0.1", author="congxu")
class getnews(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[getnews] inited")

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type != ContextType.TEXT:
            return
        
        getnews_api_token = "UDuxUGXTKAlCJ3qt"
        content = e_context['context'].content
        logger.debug("[getnews] on_handle_context. content: %s" % content)

        if re.search(r"每日新闻|getnews|今日新闻|今天有什么新闻", content):
            reply = Reply()
            reply.type = ReplyType.TEXT

            #接口信息
            url = "https://v2.alapi.cn/api/zaobao"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            payload = "token="+getnews_api_token+"&format=json"

            #获取新闻
            req = requests.request("POST", url, data=payload, headers=headers)
            news_json = json.loads(req.text) 
            news_date = news_json["data"]["date"]
            news_reasult = '\n'.join(news_json["data"]["news"])

            reply.content = f"今天是 " + news_date +"\n" + news_reasult
            
            e_context['reply'] = reply
            e_context.action = EventAction.BREAK_PASS # 事件结束，并跳过处理context的默认逻辑

        if re.search(r"每日图片|getimg|今日摄影|每日摄影", content):
            reply = Reply()
            reply.type = ReplyType.IMAGE_URL

            #获取日期信息
            # 定义日期格式的正则表达式
            date_regex = r"(\d{2,4}).?(\d{1,2}).?(\d{1,2})"

            # 定义日期格式的列表，按照优先级排序
            date_formats = ["%Y-%m-%d", "%Y.%m.%d", "%Y年%m月%d日", "%Y年的%m月%d日", "%y年%m月%d"]

#             # 使用正则表达式查找日期信息
#             match = re.search(date_regex, content)
#             if match:
#                 year, month, day = match.groups()
#                 for date_format in date_formats:
#                     try:
#                         parsed_date = datetime.strptime("{}-{}-{}".format(year, month, day), date_format)
#                         formatted_date = parsed_date.strftime("%Y-%m-%d")
#                         break
#                     except ValueError:
#                         formatted_date = datetime.now().strftime("%Y-%m-%d")
#             else:
#                 formatted_date = datetime.now().strftime("%Y-%m-%d")

            #接口信息 https://alapi.cn/api/view/10
            url = "https://v2.alapi.cn/api/bing"
            headers = {'Content-Type': "application/x-www-form-urlencoded"}
            payload = "token="+getnews_api_token+"&format=json"

            #获取新闻
            req = requests.request("POST", url, data=payload, headers=headers)
            img_json = json.loads(req.text) 
            img_reasult = img_json["data"]["url"]
            reply.content = img_reasult

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
        help_text = "输入今日新闻，获取今天新闻\n输入今日图片，获取今日摄影"
        return help_text
