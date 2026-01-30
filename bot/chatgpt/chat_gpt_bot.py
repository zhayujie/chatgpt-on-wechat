# encoding:utf-8

import time
import json

import openai
import openai.error
import requests
from common import const
from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.openai.open_ai_image import OpenAIImage
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.token_bucket import TokenBucket
from config import conf, load_config
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession

# OpenAI对话模型API (可用)
class ChatGPTBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        # set the default api_key
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("open_ai_api_base"):
            openai.api_base = conf().get("open_ai_api_base")
        proxy = conf().get("proxy")
        if proxy:
            openai.proxy = proxy
        if conf().get("rate_limit_chatgpt"):
            self.tb4chatgpt = TokenBucket(conf().get("rate_limit_chatgpt", 20))
        conf_model = conf().get("model") or "gpt-3.5-turbo"
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        # o1相关模型不支持system prompt，暂时用文心模型的session

        self.args = {
            "model": conf_model,  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # "max_tokens":4096,  # 回复最大的字符数
            "top_p": conf().get("top_p", 1),
            "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }
        # 部分模型暂不支持一些参数，特殊处理
        if conf_model in [const.O1, const.O1_MINI, const.GPT_5, const.GPT_5_MINI, const.GPT_5_NANO]:
            remove_keys = ["temperature", "top_p", "frequency_penalty", "presence_penalty"]
            for key in remove_keys:
                self.args.pop(key, None)  # 如果键不存在，使用 None 来避免抛出错、
            if conf_model in [const.O1, const.O1_MINI]:  # o1系列模型不支持系统提示词，使用文心模型的session
                self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("model") or const.O1_MINI)

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[CHATGPT] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            logger.debug("[CHATGPT] session query={}".format(session.messages))

            api_key = context.get("openai_api_key")
            model = context.get("gpt_model")
            new_args = None
            if model:
                new_args = self.args.copy()
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, api_key, args=new_args)
            logger.debug(
                "[CHATGPT] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[CHATGPT] reply {} used 0 tokens.".format(reply_content))
            return reply

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

    def reply_text(self, session: ChatGPTSession, api_key=None, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            if conf().get("rate_limit_chatgpt") and not self.tb4chatgpt.get_token():
                raise openai.error.RateLimitError("RateLimitError: rate limit exceeded")
            # if api_key == None, the default openai.api_key will be used
            if args is None:
                args = self.args
            response = openai.ChatCompletion.create(api_key=api_key, messages=session.messages, **args)
            # logger.debug("[CHATGPT] response={}".format(response))
            logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {
                "total_tokens": response["usage"]["total_tokens"],
                "completion_tokens": response["usage"]["completion_tokens"],
                "content": response.choices[0]["message"]["content"],
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.error.RateLimitError):
                logger.warn("[CHATGPT] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.error.Timeout):
                logger.warn("[CHATGPT] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIError):
                logger.warn("[CHATGPT] Bad Gateway: {}".format(e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, openai.error.APIConnectionError):
                logger.warn("[CHATGPT] APIConnectionError: {}".format(e))
                result["content"] = "我连接不到你的网络"
                if need_retry:
                    time.sleep(5)
            else:
                logger.exception("[CHATGPT] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[CHATGPT] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, api_key, args, retry_count + 1)
            else:
                return result

    def call_with_tools(self, messages, tools=None, stream=False, **kwargs):
        """
        Call OpenAI API with tool support for agent integration
        
        Args:
            messages: List of messages (may be in Claude format from agent)
            tools: List of tool definitions (may be in Claude format from agent)
            stream: Whether to use streaming
            **kwargs: Additional parameters (max_tokens, temperature, system, etc.)
            
        Returns:
            Formatted response in OpenAI format or generator for streaming
        """
        try:
            # Convert messages from Claude format to OpenAI format
            messages = self._convert_messages_to_openai_format(messages)
            
            # Convert tools from Claude format to OpenAI format
            if tools:
                tools = self._convert_tools_to_openai_format(tools)
            
            # Handle system prompt (OpenAI uses system message, Claude uses separate parameter)
            system_prompt = kwargs.get('system')
            if system_prompt:
                # Add system message at the beginning if not already present
                if not messages or messages[0].get('role') != 'system':
                    messages = [{"role": "system", "content": system_prompt}] + messages
                else:
                    # Replace existing system message
                    messages[0] = {"role": "system", "content": system_prompt}
            
            # Build request parameters
            request_params = {
                "model": kwargs.get("model", conf().get("model") or "gpt-3.5-turbo"),
                "messages": messages,
                "temperature": kwargs.get("temperature", conf().get("temperature", 0.9)),
                "top_p": kwargs.get("top_p", conf().get("top_p", 1)),
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
            
            # Handle model-specific parameters (o1, gpt-5 series don't support some params)
            model = request_params["model"]
            if model in [const.O1, const.O1_MINI, const.GPT_5, const.GPT_5_MINI, const.GPT_5_NANO]:
                remove_keys = ["temperature", "top_p", "frequency_penalty", "presence_penalty"]
                for key in remove_keys:
                    request_params.pop(key, None)
            
            # Make API call
            # Note: Don't pass api_key explicitly to use global openai.api_key and openai.api_base
            # which are set in __init__
            if stream:
                return self._handle_stream_response(request_params)
            else:
                return self._handle_sync_response(request_params)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[ChatGPT] call_with_tools error: {error_msg}")
            if stream:
                def error_generator():
                    yield {
                        "error": True,
                        "message": error_msg,
                        "status_code": 500
                    }
                return error_generator()
            else:
                return {
                    "error": True,
                    "message": error_msg,
                    "status_code": 500
                }
    
    def _handle_sync_response(self, request_params):
        """Handle synchronous OpenAI API response"""
        try:
            # Explicitly set API configuration to ensure it's used
            # (global settings can be unreliable in some contexts)
            api_key = conf().get("open_ai_api_key")
            api_base = conf().get("open_ai_api_base")
            
            # Build kwargs with explicit API configuration
            kwargs = dict(request_params)
            if api_key:
                kwargs["api_key"] = api_key
            if api_base:
                kwargs["api_base"] = api_base
            
            response = openai.ChatCompletion.create(**kwargs)
            
            # Response is already in OpenAI format
            logger.info(f"[ChatGPT] call_with_tools reply, model={response.get('model')}, "
                       f"total_tokens={response.get('usage', {}).get('total_tokens', 0)}")
            
            return response
            
        except Exception as e:
            logger.error(f"[ChatGPT] sync response error: {e}")
            raise
    
    def _handle_stream_response(self, request_params):
        """Handle streaming OpenAI API response"""
        try:
            # Explicitly set API configuration to ensure it's used
            api_key = conf().get("open_ai_api_key")
            api_base = conf().get("open_ai_api_base")
            
            logger.debug(f"[ChatGPT] Starting stream with params: model={request_params.get('model')}, stream={request_params.get('stream')}")
            
            # Build kwargs with explicit API configuration
            kwargs = dict(request_params)
            if api_key:
                kwargs["api_key"] = api_key
            if api_base:
                kwargs["api_base"] = api_base
            
            stream = openai.ChatCompletion.create(**kwargs)
            
            # OpenAI stream is already in the correct format
            chunk_count = 0
            for chunk in stream:
                chunk_count += 1
                yield chunk
            
            logger.debug(f"[ChatGPT] Stream completed, yielded {chunk_count} chunks")
                
        except Exception as e:
            logger.error(f"[ChatGPT] stream response error: {e}", exc_info=True)
            yield {
                "error": True,
                "message": str(e),
                "status_code": 500
            }
    
    def _convert_tools_to_openai_format(self, tools):
        """
        Convert tools from Claude format to OpenAI format
        
        Claude format: {name, description, input_schema}
        OpenAI format: {type: "function", function: {name, description, parameters}}
        """
        if not tools:
            return None
        
        openai_tools = []
        for tool in tools:
            # Check if already in OpenAI format
            if 'type' in tool and tool['type'] == 'function':
                openai_tools.append(tool)
            else:
                # Convert from Claude format
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "parameters": tool.get("input_schema", {})
                    }
                })
        
        return openai_tools
    
    def _convert_messages_to_openai_format(self, messages):
        """
        Convert messages from Claude format to OpenAI format
        
        Claude uses content blocks with types like 'tool_use', 'tool_result'
        OpenAI uses 'tool_calls' in assistant messages and 'tool' role for results
        """
        if not messages:
            return []
        
        openai_messages = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # Handle string content (already in correct format)
            if isinstance(content, str):
                openai_messages.append(msg)
                continue
            
            # Handle list content (Claude format with content blocks)
            if isinstance(content, list):
                # Check if this is a tool result message (user role with tool_result blocks)
                if role == "user" and any(block.get("type") == "tool_result" for block in content):
                    # Convert each tool_result block to a separate tool message
                    for block in content:
                        if block.get("type") == "tool_result":
                            openai_messages.append({
                                "role": "tool",
                                "tool_call_id": block.get("tool_use_id"),
                                "content": block.get("content", "")
                            })
                
                # Check if this is an assistant message with tool_use blocks
                elif role == "assistant":
                    # Separate text content and tool_use blocks
                    text_parts = []
                    tool_calls = []
                    
                    for block in content:
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_calls.append({
                                "id": block.get("id"),
                                "type": "function",
                                "function": {
                                    "name": block.get("name"),
                                    "arguments": json.dumps(block.get("input", {}))
                                }
                            })
                    
                    # Build OpenAI format assistant message
                    openai_msg = {
                        "role": "assistant",
                        "content": " ".join(text_parts) if text_parts else None
                    }
                    
                    if tool_calls:
                        openai_msg["tool_calls"] = tool_calls
                    
                    openai_messages.append(openai_msg)
                else:
                    # Other list content, keep as is
                    openai_messages.append(msg)
            else:
                # Other formats, keep as is
                openai_messages.append(msg)
        
        return openai_messages


class AzureChatGPTBot(ChatGPTBot):
    def __init__(self):
        super().__init__()
        openai.api_type = "azure"
        openai.api_version = conf().get("azure_api_version", "2023-06-01-preview")
        self.args["deployment_id"] = conf().get("azure_deployment_id")

    def create_img(self, query, retry_count=0, api_key=None):
        text_to_image_model = conf().get("text_to_image")
        if text_to_image_model == "dall-e-2":
            api_version = "2023-06-01-preview"
            endpoint = conf().get("azure_openai_dalle_api_base","open_ai_api_base")
            # 检查endpoint是否以/结尾
            if not endpoint.endswith("/"):
                endpoint = endpoint + "/"
            url = "{}openai/images/generations:submit?api-version={}".format(endpoint, api_version)
            api_key = conf().get("azure_openai_dalle_api_key","open_ai_api_key")
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            try:
                body = {"prompt": query, "size": conf().get("image_create_size", "256x256"),"n": 1}
                submission = requests.post(url, headers=headers, json=body)
                operation_location = submission.headers['operation-location']
                status = ""
                while (status != "succeeded"):
                    if retry_count > 3:
                        return False, "图片生成失败"
                    response = requests.get(operation_location, headers=headers)
                    status = response.json()['status']
                    retry_count += 1
                image_url = response.json()['result']['data'][0]['url']
                return True, image_url
            except Exception as e:
                logger.error("create image error: {}".format(e))
                return False, "图片生成失败"
        elif text_to_image_model == "dall-e-3":
            api_version = conf().get("azure_api_version", "2024-02-15-preview")
            endpoint = conf().get("azure_openai_dalle_api_base","open_ai_api_base")
            # 检查endpoint是否以/结尾
            if not endpoint.endswith("/"):
                endpoint = endpoint + "/"
            url = "{}openai/deployments/{}/images/generations?api-version={}".format(endpoint, conf().get("azure_openai_dalle_deployment_id","text_to_image"),api_version)
            api_key = conf().get("azure_openai_dalle_api_key","open_ai_api_key")
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            try:
                body = {"prompt": query, "size": conf().get("image_create_size", "1024x1024"), "quality": conf().get("dalle3_image_quality", "standard")}
                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()  # 检查请求是否成功
                data = response.json()

                # 检查响应中是否包含图像 URL
                if 'data' in data and len(data['data']) > 0 and 'url' in data['data'][0]:
                    image_url = data['data'][0]['url']
                    return True, image_url
                else:
                    error_message = "响应中没有图像 URL"
                    logger.error(error_message)
                    return False, "图片生成失败"

            except requests.exceptions.RequestException as e:
                # 捕获所有请求相关的异常
                try:
                    error_detail = response.json().get('error', {}).get('message', str(e))
                except ValueError:
                    error_detail = str(e)
                error_message = f"{error_detail}"
                logger.error(error_message)
                return False, error_message

            except Exception as e:
                # 捕获所有其他异常
                error_message = f"生成图像时发生错误: {e}"
                logger.error(error_message)
                return False, "图片生成失败"
        else:
            return False, "图片生成失败，未配置text_to_image参数"
