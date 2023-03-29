# encoding:utf-8

from bot.bot import Bot
from bot.openai.open_ai_image import OpenAIImage
from bot.openai.open_ai_session import OpenAISession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import conf
from common.log import logger
import openai
import openai.error
import time

user_session = dict()

# OpenAI对话模型API (可用)
class OpenAIBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        openai.api_key = conf().get('open_ai_api_key')
        if conf().get('open_ai_api_base'):
            openai.api_base = conf().get('open_ai_api_base')
        proxy = conf().get('proxy')
        if proxy:
            openai.proxy = proxy

        self.sessions = SessionManager(OpenAISession, model= conf().get("model") or "text-davinci-003")

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[OPEN_AI] query={}".format(query))
                session_id = context['session_id']
                reply = None
                if query == '#清除记忆':
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, '记忆已清除')
                elif query == '#清除所有':
                    self.sessions.clear_all_session()
                    reply = Reply(ReplyType.INFO, '所有人记忆已清除')
                else:
                    session = self.sessions.session_query(query, session_id)
                    new_query = str(session)
                    logger.debug("[OPEN_AI] session query={}".format(new_query))

                    total_tokens, completion_tokens, reply_content = self.reply_text(new_query, session_id, 0)
                    logger.debug("[OPEN_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(new_query, session_id, reply_content, completion_tokens))

                    if total_tokens == 0 :
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

    def reply_text(self, query, session_id, retry_count=0):
        try:
            response = openai.Completion.create(
                model= conf().get("model") or "text-davinci-003",  # 对话模型的名称
                prompt=query,
                temperature=0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
                max_tokens=1200,  # 回复最大的字符数
                top_p=1,
                frequency_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                presence_penalty=0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
                stop=["\n\n\n"]
            )
            res_content = response.choices[0]['text'].strip().replace('<|endoftext|>', '')
            total_tokens = response["usage"]["total_tokens"]
            completion_tokens = response["usage"]["completion_tokens"]
            logger.info("[OPEN_AI] reply={}".format(res_content))
            return total_tokens, completion_tokens, res_content
        except Exception as e:
            need_retry = retry_count < 2
            result = [0,0,"我现在有点累了，等会再来吧"]
            if isinstance(e, openai.error.RateLimitError):
                logger.warn("[OPEN_AI] RateLimitError: {}".format(e))
                result[2] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.Timeout):
                logger.warn("[OPEN_AI] Timeout: {}".format(e))
                result[2] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIConnectionError):
                logger.warn("[OPEN_AI] APIConnectionError: {}".format(e))
                need_retry = False
                result[2] = "我连接不到你的网络"
            else:
                logger.warn("[OPEN_AI] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session_id)

            if need_retry:
                logger.warn("[OPEN_AI] 第{}次重试".format(retry_count+1))
                return self.reply_text(query, session_id, retry_count+1)
            else:
                return result