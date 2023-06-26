# access LinkAI knowledge base platform
# docs: https://link-ai.tech/platform/link-app/wechat

import time

import requests

from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.openai.open_ai_image import OpenAIImage
from bot.session_manager import SessionManager
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf


class LinkAIBot(Bot, OpenAIImage):
    # authentication failed
    AUTH_FAILED_CODE = 401
    NO_QUOTA_CODE = 406

    def __init__(self):
        super().__init__()
        self.base_url = "https://api.link-ai.chat/v1"
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")

    def reply(self, query, context: Context = None) -> Reply:
        if context.type == ContextType.TEXT:
            return self._chat(query, context)
        elif context.type == ContextType.IMAGE_CREATE:
            ok, retstring = self.create_img(query, 0)
            reply = None
            if ok:
                reply = Reply(ReplyType.IMAGE_URL, retstring)
            else:
                reply = Reply(ReplyType.ERROR, retstring)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def _chat(self, query, context, retry_count=0):
        if retry_count >= 2:
            # exit from retry 2 times
            logger.warn("[LINKAI] failed after maximum number of retry times")
            return Reply(ReplyType.ERROR, "请再问我一次吧")

        try:
            # load config
            if context.get("generate_breaked_by"):
                logger.info(f"[LINKAI] won't set appcode because a plugin ({context['generate_breaked_by']}) affected the context")
                app_code = None
            else:
                app_code = conf().get("linkai_app_code")
            linkai_api_key = conf().get("linkai_api_key")

            session_id = context["session_id"]

            session = self.sessions.session_query(query, session_id)

            # remove system message
            if app_code and session.messages[0].get("role") == "system":
                session.messages.pop(0)

            logger.info(f"[LINKAI] query={query}, app_code={app_code}")

            body = {
                "appCode": app_code,
                "messages": session.messages,
                "model": conf().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
                "temperature": conf().get("temperature"),
                "top_p": conf().get("top_p", 1),
                "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            }
            headers = {"Authorization": "Bearer " + linkai_api_key}

            # do http request
            res = requests.post(url=self.base_url + "/chat/completion", json=body, headers=headers).json()

            if not res or not res["success"]:
                if res.get("code") == self.AUTH_FAILED_CODE:
                    logger.exception(f"[LINKAI] please check your linkai_api_key, res={res}")
                    return Reply(ReplyType.ERROR, "请再问我一次吧")

                elif res.get("code") == self.NO_QUOTA_CODE:
                    logger.exception(f"[LINKAI] please check your account quota, https://chat.link-ai.tech/console/account")
                    return Reply(ReplyType.ERROR, "提问太快啦，请休息一下再问我吧")

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
