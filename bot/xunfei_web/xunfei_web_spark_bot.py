from bot.bot import Bot
from bot.session_manager import SessionManager
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from common import const
import queue
import threading
import random

# 假设这是从您项目中导入的SparkWeb类
from sparkdesk_web.core import SparkWeb

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
            logger.info("[XunFeiWeb] query={}".format(query))
            session_id = context["session_id"]
            # 使用SparkWeb进行持续对话
            chat = self.sparkWeb.create_continuous_chat()
            reply_content = chat.chat(input="Ask: " + query)
            reply = Reply(ReplyType.TEXT, reply_content)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

# 注意：这里的实现基于假设的`SparkWeb`类接口，实际应用中需根据`SparkWeb`的实际定义调整