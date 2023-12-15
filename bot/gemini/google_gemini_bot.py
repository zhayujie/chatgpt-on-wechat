"""
Google gemini bot

@author zhayujie
@Date 2023/12/15
"""
# encoding:utf-8

from bot.bot import Bot
import google.generativeai as genai
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession


# OpenAI对话模型API (可用)
class GoogleGeminiBot(Bot):

    def __init__(self):
        super().__init__()
        self.api_key = conf().get("gemini_api_key")
        # 复用文心的token计算方式
        self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("model") or "gpt-3.5-turbo")

    def reply(self, query, context: Context = None) -> Reply:
        if context.type != ContextType.TEXT:
            logger.warn(f"[Gemini] Unsupported message type, type={context.type}")
            return Reply(ReplyType.TEXT, None)
        logger.info(f"[Gemini] query={query}")
        session_id = context["session_id"]
        session = self.sessions.session_query(query, session_id)
        gemini_messages = self._convert_to_gemini_messages(session.messages)
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(gemini_messages)
        reply_text = response.text
        self.sessions.session_reply(reply_text, session_id)
        logger.info(f"[Gemini] reply={reply_text}")
        return Reply(ReplyType.TEXT, reply_text)


    def _convert_to_gemini_messages(self, messages: list):
        res = []
        for msg in messages:
            if msg.get("role") == "user":
                role = "user"
            elif msg.get("role") == "assistant":
                role = "model"
            else:
                continue
            res.append({
                "role": role,
                "parts": [{"text": msg.get("content")}]
            })
        return res
