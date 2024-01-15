# encoding:utf-8

import time

import openai
import openai.error

    
import requests
import logging
import time

from bot.bot import Bot
from bot.openai.open_ai_image import OpenAIImage
from bot.openai.open_ai_session import OpenAISession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf ,get_random_key


user_session = dict()


# OpenAI对话模型API (可用)
class OpenAIBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        # openai.api_key = conf().get("open_ai_api_key")
        openai.api_key = get_random_key()
        if conf().get("open_ai_api_base"):
            openai.api_base = conf().get("open_ai_api_base")
        proxy = conf().get("proxy")
        
        if proxy:
            openai.proxy = proxy

        self.sessions = SessionManager(OpenAISession, model=conf().get("model") or "text-davinci-003")
        self.args = {
            "model": conf().get("model") or "text-davinci-003",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            "max_tokens": 1200,  # 回复最大的字符数
            "top_p": 1,
            "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
            "stop": ["\n\n\n"],
        }

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[OPEN_AI] query={}".format(query))
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
                        "[OPEN_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(str(session), session_id, reply_content, completion_tokens)
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

    # def reply_text(self, session: OpenAISession, retry_count=0):
    #     try:
    #         api_key = get_random_key()
    #         response = openai.Completion.create(prompt=str(session),api_key, **self.args)
    #         res_content = response.choices[0]["text"].strip().replace("<|endoftext|>", "")
    #         total_tokens = response["usage"]["total_tokens"]
    #         completion_tokens = response["usage"]["completion_tokens"]
    #         logger.info("[OPEN_AI] reply={}".format(res_content))
    #         return {
    #             "total_tokens": total_tokens,
    #             "completion_tokens": completion_tokens,
    #             "content": res_content,
    #         }
    #     except Exception as e:
    #         need_retry = retry_count < 2
    #         result = {"completion_tokens": 0, "content": e}
    #         if isinstance(e, openai.error.RateLimitError):
    #             logger.warn("[OPEN_AI] RateLimitError: {}".format(e))
    #             result["content"] = "提问太快啦，请休息一下再问我吧"
    #             if need_retry:
    #                 time.sleep(20)
    #         elif isinstance(e, openai.error.Timeout):
    #             logger.warn("[OPEN_AI] Timeout: {}".format(e))
    #             result["content"] = "我没有收到你的消息"
    #             if need_retry:
    #                 time.sleep(5)
    #         elif isinstance(e, openai.error.APIConnectionError):
    #             logger.warn("[OPEN_AI] APIConnectionError: {}".format(e))
    #             need_retry = False
    #             result["content"] = "我连接不到你的网络"
    #         else:
    #             logger.warn("[OPEN_AI] Exception: {}".format(e))
    #             need_retry = False
    #             self.sessions.clear_session(session.session_id)

    #         if need_retry:
    #             logger.warn("[OPEN_AI] 第{}次重试".format(retry_count + 1))
    #             return self.reply_text(session, retry_count + 1)
    #         else:
    #             return result
    
    def reply_text(self, session: OpenAISession, retry_count=0):
        try:
            api_key = get_random_key()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # Get session history and summarize
            history = session.get_history()
            summary = " ".join([msg.content for msg in history])
            summary = summary[:200]  # Ensure the summary is within 200 characters
            
            payload = {
                "prompt": summary,
                **self.args
            }
            proxy_new= self.proxy+'/v1/engines/davinci-codex/completions'
            response = requests.post(proxy_new, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            

    
            # Process the API response
            res_content = result["choices"][0]["text"].strip().replace("...", "")
            total_tokens = result["usage"]["total_tokens"]
            completion_tokens = result["usage"]["completion_tokens"]
            logger.info("[OPEN_AI] reply={}".format(res_content))
            
            # Return the result
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            # Handle exceptions such as API errors or network issues
            logger.error("尝试从OpenAI获取回复时出错：{}".format(e))
            if retry_count < self.max_retries:
                logger.info("正在重试... (尝试次数 {})".format(retry_count + 1))
                time.sleep(retry_count + 1)  # Exponential backoff
                return self.reply_text(session, retry_count=retry_count + 1)
            else:
                logger.error("已达到最大重试次数，放弃重试。")
                return {
                    "total_tokens": 0,
                    "completion_tokens": 0,
                    "content": "对不起，我现在处理您的请求有些困难。",
                }
    
    # ... 可能还有其他的类或函数定义 ...
    
        
