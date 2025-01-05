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
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from bot.bot import Bot
import google.generativeai as genai
from bot.session_manager import SessionManager
...
import time  # 新增 time 库


# OpenAI对话模型API (可用)
class GoogleGeminiBot(Bot):

    def __init__(self):
        super().__init__()
        self.api_key = conf().get("gemini_api_key")
        # 复用chatGPT的token计算方式
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.model = conf().get("model") or "gemini-pro"
        if self.model == "gemini":
            self.model = "gemini-pro"
    def reply(self, query, context: Context = None) -> Reply:
        try:
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            media_file = None        
            if context.type == ContextType.TEXT:
                gemini_messages = self._convert_to_gemini_messages(self.filter_messages(session.messages))
            elif context.type == ContextType.IMAGE:
                media_file = genai.upload_file(context.content)
            elif context.type == ContextType.AUDIO:
                media_file = genai.upload_file(context.content)
            elif context.type == ContextType.VIDEO:
                media_file = genai.upload_file(context.content)
                while media_file.state.name == "PROCESSING":
                    time.sleep(5)  # 视频处理中,等待5秒后再查询状态
                    media_file = genai.get_file(media_file.name)
            else:
                raise ValueError(f"Unsupported input type: {context.type}")
            if media_file:
                gemini_messages = [media_file, "\n\n", query]
            else:
                gemini_messages = self._convert_to_gemini_messages(query)
            
            # 添加安全设置
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # 生成回复，包含安全设置
            response = model.generate_content(
                gemini_messages,
                safety_settings=safety_settings
            )
            if response.candidates and response.candidates[0].content:
                reply_text = response.candidates[0].content.parts[0].text
                logger.info(f"[Gemini] reply={reply_text}") 
                self.sessions.session_reply(reply_text, session_id)
                return Reply(ReplyType.TEXT, reply_text)
            else:
                logger.warning("[Gemini] No valid response generated.")
                error_message = "No valid response generated."
                self.sessions.session_reply(error_message, session_id)
                return Reply(ReplyType.ERROR, error_message)
                    
        except Exception as e:
            logger.error(f"[Gemini] Error generating response: {str(e)}", exc_info=True)
            error_message = "Failed to invoke [Gemini] api!"
            self.sessions.session_reply(error_message, session_id)
            return Reply(ReplyType.ERROR, error_message)
            
    def _convert_to_gemini_messages(self, messages):
        if isinstance(messages, str):
            return [{"role": "user", "parts": [{"text": messages}]}]
        res = []
        for msg in messages:
            if msg.get("role") == "user":
                role = "user"
            elif msg.get("role") == "assistant":
                role = "model" 
            elif msg.get("role") == "system":
                role = "user"
            else:
                continue
            res.append({"role": role,
            "parts": [{"text": msg.get("content")}]
            })
        return res

    @staticmethod
    def filter_messages(messages: list):
        res = []
        turn = "user"
        if not messages:
            return res
        for i in range(len(messages) - 1, -1, -1):
            message = messages[i]
            role = message.get("role")
            if role == "system":
                res.insert(0, message)
                continue
            if role != turn:
                continue
            res.insert(0, message)
            if turn == "user":
                turn = "assistant"
            elif turn == "assistant":
                turn = "user"
        return res
