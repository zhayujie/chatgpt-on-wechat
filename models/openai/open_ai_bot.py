# encoding:utf-8

import time

import openai
import openai.error

from models.bot import Bot
from models.openai_compatible_bot import OpenAICompatibleBot
from models.openai.open_ai_image import OpenAIImage
from models.openai.open_ai_session import OpenAISession
from models.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf

user_session = dict()


# OpenAI对话模型API (可用)
class OpenAIBot(Bot, OpenAIImage, OpenAICompatibleBot):
    def __init__(self):
        super().__init__()
        openai.api_key = conf().get("open_ai_api_key")
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
    
    def get_api_config(self):
        """Get API configuration for OpenAI-compatible base class"""
        return {
            'api_key': conf().get("open_ai_api_key"),
            'api_base': conf().get("open_ai_api_base"),
            'model': conf().get("model", "text-davinci-003"),
            'default_temperature': conf().get("temperature", 0.9),
            'default_top_p': conf().get("top_p", 1.0),
            'default_frequency_penalty': conf().get("frequency_penalty", 0.0),
            'default_presence_penalty': conf().get("presence_penalty", 0.0),
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

    def reply_text(self, session: OpenAISession, retry_count=0):
        try:
            response = openai.Completion.create(prompt=str(session), **self.args)
            res_content = response.choices[0]["text"].strip().replace("<|endoftext|>", "")
            total_tokens = response["usage"]["total_tokens"]
            completion_tokens = response["usage"]["completion_tokens"]
            logger.info("[OPEN_AI] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.error.RateLimitError):
                logger.warn("[OPEN_AI] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.error.Timeout):
                logger.warn("[OPEN_AI] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIConnectionError):
                logger.warn("[OPEN_AI] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                logger.warn("[OPEN_AI] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[OPEN_AI] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result

    def call_with_tools(self, messages, tools=None, stream=False, **kwargs):
        """
        Call OpenAI API with tool support for agent integration
        Note: This bot uses the old Completion API which doesn't support tools.
        For tool support, use ChatGPTBot instead.
        
        This method converts to ChatCompletion API when tools are provided.
        
        Args:
            messages: List of messages
            tools: List of tool definitions (OpenAI format)
            stream: Whether to use streaming
            **kwargs: Additional parameters
            
        Returns:
            Formatted response in OpenAI format or generator for streaming
        """
        try:
            # The old Completion API doesn't support tools
            # We need to use ChatCompletion API instead
            logger.info("[OPEN_AI] Using ChatCompletion API for tool support")
            
            # Build request parameters for ChatCompletion
            request_params = {
                "model": kwargs.get("model", conf().get("model") or "gpt-4.1"),
                "messages": messages,
                "temperature": kwargs.get("temperature", conf().get("temperature", 0.9)),
                "top_p": kwargs.get("top_p", 1),
                "frequency_penalty": kwargs.get("frequency_penalty", conf().get("frequency_penalty", 0.0)),
                "presence_penalty": kwargs.get("presence_penalty", conf().get("presence_penalty", 0.0)),
                "stream": stream
            }
            
            # Add max_tokens if specified
            if kwargs.get("max_tokens"):
                request_params["max_tokens"] = kwargs["max_tokens"]
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = kwargs.get("tool_choice", "auto")
            
            # Make API call using ChatCompletion
            if stream:
                return self._handle_stream_response(request_params)
            else:
                return self._handle_sync_response(request_params)
                
        except Exception as e:
            logger.error(f"[OPEN_AI] call_with_tools error: {e}")
            if stream:
                def error_generator():
                    yield {
                        "error": True,
                        "message": str(e),
                        "status_code": 500
                    }
                return error_generator()
            else:
                return {
                    "error": True,
                    "message": str(e),
                    "status_code": 500
                }
    
    def _handle_sync_response(self, request_params):
        """Handle synchronous OpenAI ChatCompletion API response"""
        try:
            response = openai.ChatCompletion.create(**request_params)
            
            logger.info(f"[OPEN_AI] call_with_tools reply, model={response.get('model')}, "
                       f"total_tokens={response.get('usage', {}).get('total_tokens', 0)}")
            
            return response
            
        except Exception as e:
            logger.error(f"[OPEN_AI] sync response error: {e}")
            raise
    
    def _handle_stream_response(self, request_params):
        """Handle streaming OpenAI ChatCompletion API response"""
        try:
            stream = openai.ChatCompletion.create(**request_params)
            
            for chunk in stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"[OPEN_AI] stream response error: {e}")
            yield {
                "error": True,
                "message": str(e),
                "status_code": 500
            }
