from bot.bot import Bot
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from bridge.context import Context
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.session_manager import SessionManager
from config import conf
import requests
import time

class LinkAIBot(Bot):

    # authentication failed
    AUTH_FAILED_CODE = 401

    def __init__(self):
        self.base_url = "https://api.link-ai.chat/v1"
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")

    def reply(self, query, context: Context = None) -> Reply:
        return self._chat(query, context)

    def _chat(self, query, context, retry_count=0):
        if retry_count >= 2:
            # exit from retry 2 times
            logger.warn("[LINKAI] failed after maximum number of retry times")
            return Reply(ReplyType.ERROR, "请再问我一次吧")

        try:
            session_id = context["session_id"]

            session = self.sessions.session_query(query, session_id)

            # remove system message
            if session.messages[0].get("role") == "system":
                session.messages.pop(0)

            # load config
            app_code = conf().get("linkai_app_code")
            linkai_api_key = conf().get("linkai_api_key")
            logger.info(f"[LINKAI] query={query}, app_code={app_code}")

            body = {
                "appCode": app_code,
                "messages": session.messages
            }
            headers = {"Authorization": "Bearer " + linkai_api_key}

            # do http request
            res = requests.post(url=self.base_url + "/chat/completion", json=body, headers=headers).json()

            if not res or not res["success"]:
                if res.get("code") == self.AUTH_FAILED_CODE:
                    logger.exception(f"[LINKAI] please check your linkai_api_key, res={res}")
                    return Reply(ReplyType.ERROR, "请再问我一次吧")
                else:
                    # retry
                    time.sleep(2)
                    logger.warn(f"[LINKAI] do retry, times={retry_count}")
                    return self._chat(query, context, retry_count + 1)
            # execute success
            reply_content = res["data"]["content"]
            logger.info(f"[LINKAI] reply={reply_content}")
            self.sessions.session_reply(reply_content, session_id)
            return Reply(ReplyType.TEXT, reply_content)
        except Exception as e:
            logger.exception(e)
            # retry
            time.sleep(2)
            logger.warn(f"[LINKAI] do retry, times={retry_count}")
            return self._chat(query, context, retry_count + 1)
