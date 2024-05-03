
from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
import ollama


# Ollama对话模型API (可用)
class OllamaBot(Bot):

    def __init__(self):
        super().__init__()
        self.model = conf().get("model") or "gemma:7b"
        # 复用文心的token计算方式
        self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("model") or "gemma:7b")

    def reply(self, query, context: Context = None) -> Reply:
        try:
            if context.type != ContextType.TEXT:
                logger.warn(f"[Ollama-{self.model}] Unsupported message type, type={context.type}")
                return Reply(ReplyType.TEXT, None)
            logger.info(f"[Ollama-{self.model}] query={query}")
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            # 这里直接调用本地的Ollama服务
            response = ollama.chat(
                model=self.model,
                messages=self.filter_messages(session.messages))
            reply_text = response['message']['content']
            self.sessions.session_reply(reply_text, session_id)
            logger.info(f"[Ollama-{self.model}] reply={reply_text}")
            return Reply(ReplyType.TEXT, reply_text)
        except Exception as e:
            logger.error("f[Ollama-{self.model}] fetch reply error, may contain unsafe content")
            logger.error(e)
            return Reply(ReplyType.ERROR, f"Ollama failed{e}")

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

    @staticmethod
    def filter_messages(messages: list):
        res = []
        turn = "user"
        if not messages:
            return res
        for i in range(len(messages) - 1, -1, -1):
            message = messages[i]
            if message.get("role") != turn:
                continue
            res.insert(0, message)
            if turn == "user":
                turn = "assistant"
            elif turn == "assistant":
                turn = "user"
        return res
