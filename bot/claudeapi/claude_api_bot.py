# encoding:utf-8

import time

import openai
import openai.error
import anthropic

from bot.bot import Bot
from bot.openai.open_ai_image import OpenAIImage
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common import const
from config import conf

user_session = dict()


# OpenAI对话模型API (可用)
class ClaudeAPIBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        proxy = conf().get("proxy", None)
        base_url = conf().get("open_ai_api_base", None)  # 复用"open_ai_api_base"参数作为base_url
        self.claudeClient = anthropic.Anthropic(
            api_key=conf().get("claude_api_key"),
            proxies=proxy if proxy else None,
            base_url=base_url if base_url else None
        )
        self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("model") or "text-davinci-003")

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[CLAUDE_API] query={}".format(query))
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
                    logger.info(result)
                    total_tokens, completion_tokens, reply_content = (
                        result["total_tokens"],
                        result["completion_tokens"],
                        result["content"],
                    )
                    logger.debug(
                        "[CLAUDE_API] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(str(session), session_id, reply_content, completion_tokens)
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

    def reply_text(self, session: BaiduWenxinSession, retry_count=0):
        try:
            actual_model = self._model_mapping(conf().get("model"))
            response = self.claudeClient.messages.create(
                model=actual_model,
                max_tokens=4096,
                system=conf().get("character_desc", ""),
                messages=session.messages
            )
            # response = openai.Completion.create(prompt=str(session), **self.args)
            res_content = response.content[0].text.strip().replace("<|endoftext|>", "")
            total_tokens = response.usage.input_tokens+response.usage.output_tokens
            completion_tokens = response.usage.output_tokens
            logger.info("[CLAUDE_API] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"total_tokens": 0, "completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.error.RateLimitError):
                logger.warn("[CLAUDE_API] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.error.Timeout):
                logger.warn("[CLAUDE_API] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIConnectionError):
                logger.warn("[CLAUDE_API] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                logger.warn("[CLAUDE_API] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[CLAUDE_API] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result

    def _model_mapping(self, model) -> str:
        if model == "claude-3-opus":
            return const.CLAUDE_3_OPUS
        elif model == "claude-3-sonnet":
            return const.CLAUDE_3_SONNET
        elif model == "claude-3-haiku":
            return const.CLAUDE_3_HAIKU
        elif model == "claude-3.5-sonnet":
            return const.CLAUDE_35_SONNET
        return model
