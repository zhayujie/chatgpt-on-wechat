# encoding:utf-8

import requests
import json
from common import const
from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.coze.coze_session import CozeSession

COZE_API_KEY = conf().get("coze_api_key")
COZE_BOT_ID = conf().get("coze_bot_id")

class CozeBot(Bot):

    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(CozeSession, model="coze")

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                # logger.info("[COZE] query={}".format(query))
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
                    result = self.reply_text(query)
                    total_tokens, completion_tokens, reply_content = (
                        result["total_tokens"],
                        result["completion_tokens"],
                        result["content"],
                    )
                    logger.debug(
                        "[COZE] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(session.messages, session_id, reply_content, completion_tokens)
                    )

                    if total_tokens == 0:
                        reply = Reply(ReplyType.ERROR, reply_content)
                    else:
                        self.sessions.session_reply(reply_content, session_id, total_tokens)
                        reply = Reply(ReplyType.TEXT, reply_content)
                return reply
            elif context.type == ContextType.IMAGE_CREATE:
                ok, retstring = self.create_img(query, 0)
                reply = None
                if ok:
                    reply = Reply(ReplyType.IMAGE_URL, retstring)
                else:
                    reply = Reply(ReplyType.ERROR, retstring)
                return reply

    def reply_text(self, session: str, retry_count=0):
        try:
            # logger.info("[COZE] model={}".format(session.model))
            url = "https://api.coze.cn/open_api/v2/chat"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + COZE_API_KEY
            }
            payload = {
                'query': session,
                "conversation_id": "keep",
                'user': "keep",
                "bot_id": COZE_BOT_ID,
                "stream": False
            }
            print(payload["query"])
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            response_text = json.loads(response.text)
            # logger.info(f"[COZE] response text={response_text}")
            res_content = response_text["messages"][1]["content"]
            total_tokens = 1
            completion_tokens = 1
            # logger.info("[COZE] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            logger.warn("[COZE] Exception: {}".format(e))
            need_retry = False
            self.sessions.clear_session(session.session_id)
            result = {"total_tokens": 0, "completion_tokens": 0, "content": "出错了: {}".format(e)}
            return result