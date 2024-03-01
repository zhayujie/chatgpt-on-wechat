# encoding:utf-8

import time

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from bot.bot import Bot
from bot.mistral.mistralai_session import MistralAISession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf

user_session = dict()


# OpenAI对话模型API (可用)
class MistralAIBot(Bot):
    def __init__(self):
        super().__init__()
        api_key = conf().get("mistralai_api_key")
        self.client = MistralClient(api_key=api_key)
        self.system_prompt = conf().get("character_desc", "")
        self.sessions = SessionManager(MistralAISession, model=conf().get("model") or "mistral-large-latest")
        self.model = conf().get("model") or "mistral-large-latest"  # 对话模型的名称
        self.temperature = conf().get("temperature", 0.7)  # 值在[0,1]之间，越大表示回复越具有不确定性
        self.top_p = conf().get("top_p", 1)
        self.safe_prompt = True
        logger.info("[MISTRAL_AI] Create finish.")

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[MISTRAL_AI] query={}".format(query))
                session_id = context["session_id"]
                reply = None
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                elif query == "#清除所有":
                    self.sessions.clear_all_session()
                    reply = Reply(ReplyType.INFO, "所有人记忆已清除")
                else:
                    session = self.sessions.session_query(query, session_id)
                    result = self.reply_text(session)
                    total_tokens, completion_tokens, reply_content = (
                        result["total_tokens"],
                        result["completion_tokens"],
                        result["content"],
                    )
                    logger.debug(
                        "[MISTRAL_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(str(session), session_id, reply_content, completion_tokens)
                    )

                    if total_tokens == 0:
                        reply = Reply(ReplyType.ERROR, reply_content)
                    else:
                        self.sessions.session_reply(reply_content, session_id, total_tokens)
                        reply = Reply(ReplyType.TEXT, reply_content)
                return reply
            else:
                logger.info("[MISTRAL_AI] context={}".format(context))

    def reply_text(self, session: MistralAISession):
        try:
            messages = self._convert_to_mistral_messages(self._filter_messages(session.messages))
            response = self.client.chat(messages, temperature=self.temperature, model=self.model,
                                        top_p=self.top_p, safe_prompt=self.safe_prompt)
            res_content = response.choices[0].message.content
            total_tokens = response.usage.total_tokens
            completion_tokens = response.usage.completion_tokens
            logger.info("[MISTRAL_AI] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            result = {"total_tokens": 0, "completion_tokens": 0, "content": "我刚刚开小差了，请稍后再试一下"}
            logger.warn("[MISTRAL_AI] Exception: {}".format(e))
            return result

    def _convert_to_mistral_messages(self, messages: list):
        res = []
        res.append(ChatMessage(role="system", content=self.system_prompt))
        for msg in messages:
            if msg.get("role") == "user":
                role = "user"
            elif msg.get("role") == "assistant":
                role = "model"
            else:
                continue
            res.append(
                ChatMessage(role=role, content=msg.get("content")))
        return res

    def _filter_messages(self, messages: list):
        res = []
        turn = "user"
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