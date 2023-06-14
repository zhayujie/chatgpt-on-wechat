# encoding:utf-8

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *

import schedule
import time


@plugins.register(
    name="ScheduledMessage",
    desire_priority=-1,
    hidden=True,
    desc="A plugin that sends scheduled messages",
    version="0.1",
    author="kevintao",
)
class ScheduledMessage(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_SCHEDULED_MESSAGE] = self.on_scheduled_message
        self.start_scheduled_message_job()
        logger.info("[ScheduledMessage] inited")

    def start_scheduled_message_job(self):
        # 设置定时任务：每天18:00发送一条消息
        # schedule.every().day.at("18:00").do(self.send_scheduled_message)
        # 设置定时任务：每10秒
        schedule.every(10).seconds.do(self.send_scheduled_message)

        # 启动定时任务的调度循环
        while True:
            schedule.run_pending()
            time.sleep(1)

    def send_scheduled_message(self):
        # 创建一个 Context 对象和 Reply 对象，用于发送消息
        context = Context(type=ContextType.TEXT, content="Scheduled message")
        reply = Reply(type=ReplyType.TEXT, content="This is a scheduled message")

        # 调用 _send_reply 函数发送消息
        self._send_reply(context, reply)

    def on_scheduled_message(self, e_context: EventContext):
        # 可以在此方法中处理定时消息的相关事件
        # 可以访问 e_context["channel"] 和 e_context["context"] 来获取相关信息
        pass
