"""
Google gemini bot

@author zhayujie
@Date 2023/12/15
"""
# encoding:utf-8

import json
import time
from bot.bot import Bot
import google.generativeai as genai
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from google.generativeai.types import HarmCategory, HarmBlockThreshold


# OpenAI对话模型API (可用)
class GoogleGeminiBot(Bot):

    def __init__(self):
        super().__init__()
        self.api_key = conf().get("gemini_api_key")
        # 复用chatGPT的token计算方式
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-3.5-turbo")
        self.model = conf().get("model") or "gemini-pro"
        if self.model == "gemini":
            self.model = "gemini-pro"
    def reply(self, query, context: Context = None) -> Reply:
        try:
            if context.type != ContextType.TEXT:
                logger.warn(f"[Gemini] Unsupported message type, type={context.type}")
                return Reply(ReplyType.TEXT, None)
            logger.info(f"[Gemini] query={query}")
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            gemini_messages = self._convert_to_gemini_messages(self.filter_messages(session.messages))
            logger.debug(f"[Gemini] messages={gemini_messages}")
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            # 添加安全设置
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # 生成回复，包含安全设置
            response = model.generate_content(
                gemini_messages,
                safety_settings=safety_settings
            )
            if response.candidates and response.candidates[0].content:
                reply_text = response.candidates[0].content.parts[0].text
                logger.info(f"[Gemini] reply={reply_text}")
                self.sessions.session_reply(reply_text, session_id)
                return Reply(ReplyType.TEXT, reply_text)
            else:
                # 没有有效响应内容，可能内容被屏蔽，输出安全评分
                logger.warning("[Gemini] No valid response generated. Checking safety ratings.")
                if hasattr(response, 'candidates') and response.candidates:
                    for rating in response.candidates[0].safety_ratings:
                        logger.warning(f"Safety rating: {rating.category} - {rating.probability}")
                error_message = "No valid response generated due to safety constraints."
                self.sessions.session_reply(error_message, session_id)
                return Reply(ReplyType.ERROR, error_message)
                    
        except Exception as e:
            logger.error(f"[Gemini] Error generating response: {str(e)}", exc_info=True)
            error_message = "Failed to invoke [Gemini] api!"
            self.sessions.session_reply(error_message, session_id)
            return Reply(ReplyType.ERROR, error_message)
            
    def _convert_to_gemini_messages(self, messages: list):
        res = []
        for msg in messages:
            if msg.get("role") == "user":
                role = "user"
            elif msg.get("role") == "assistant":
                role = "model"
            elif msg.get("role") == "system":
                role = "user"
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
            role = message.get("role")
            if role == "system":
                res.insert(0, message)
                continue
            if role != turn:
                continue
            res.insert(0, message)
            if turn == "user":
                turn = "assistant"
            elif turn == "assistant":
                turn = "user"
        return res

    def call_with_tools(self, messages, tools=None, stream=False, **kwargs):
        """
        Call Gemini API with tool support for agent integration
        
        Args:
            messages: List of messages
            tools: List of tool definitions (OpenAI format, will be converted to Gemini format)
            stream: Whether to use streaming
            **kwargs: Additional parameters
            
        Returns:
            Formatted response compatible with OpenAI format or generator for streaming
        """
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            model_name = kwargs.get("model", self.model)
            
            # Extract system prompt from messages
            system_prompt = kwargs.get("system", "")
            gemini_messages = []
            
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg["content"]
                else:
                    gemini_messages.append(msg)
            
            # Convert messages to Gemini format
            gemini_messages = self._convert_to_gemini_messages(gemini_messages)
            
            # Safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # Convert tools from OpenAI format to Gemini format if provided
            gemini_tools = None
            if tools:
                gemini_tools = self._convert_tools_to_gemini_format(tools)
            
            # Create model with system instruction if available
            model_kwargs = {"model_name": model_name}
            if system_prompt:
                model_kwargs["system_instruction"] = system_prompt
            
            model = genai.GenerativeModel(**model_kwargs)
            
            # Generate content
            generation_config = {}
            if kwargs.get("max_tokens"):
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            if kwargs.get("temperature") is not None:
                generation_config["temperature"] = kwargs["temperature"]
            
            request_params = {
                "safety_settings": safety_settings
            }
            if generation_config:
                request_params["generation_config"] = generation_config
            if gemini_tools:
                request_params["tools"] = gemini_tools
            
            if stream:
                return self._handle_gemini_stream_response(model, gemini_messages, request_params, model_name)
            else:
                return self._handle_gemini_sync_response(model, gemini_messages, request_params, model_name)
                
        except Exception as e:
            logger.error(f"[Gemini] call_with_tools error: {e}")
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
    
    def _convert_tools_to_gemini_format(self, openai_tools):
        """Convert OpenAI tool format to Gemini function declarations"""
        import google.generativeai as genai
        
        gemini_functions = []
        for tool in openai_tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                gemini_functions.append(
                    genai.protos.FunctionDeclaration(
                        name=func.get("name"),
                        description=func.get("description", ""),
                        parameters=func.get("parameters", {})
                    )
                )
        
        if gemini_functions:
            return [genai.protos.Tool(function_declarations=gemini_functions)]
        return None
    
    def _handle_gemini_sync_response(self, model, messages, request_params, model_name):
        """Handle synchronous Gemini API response"""
        import json
        
        response = model.generate_content(messages, **request_params)
        
        # Extract text content and function calls
        text_content = ""
        tool_calls = []
        
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    text_content += part.text
                elif hasattr(part, 'function_call') and part.function_call:
                    # Convert Gemini function call to OpenAI format
                    func_call = part.function_call
                    tool_calls.append({
                        "id": f"call_{hash(func_call.name)}",
                        "type": "function",
                        "function": {
                            "name": func_call.name,
                            "arguments": json.dumps(dict(func_call.args))
                        }
                    })
        
        # Build message in OpenAI format
        message = {
            "role": "assistant",
            "content": text_content
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        # Format response to match OpenAI structure
        formatted_response = {
            "id": f"gemini_{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": message,
                    "finish_reason": "stop" if not tool_calls else "tool_calls"
                }
            ],
            "usage": {
                "prompt_tokens": 0,  # Gemini doesn't provide token counts in the same way
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        
        logger.info(f"[Gemini] call_with_tools reply, model={model_name}")
        return formatted_response
    
    def _handle_gemini_stream_response(self, model, messages, request_params, model_name):
        """Handle streaming Gemini API response"""
        import json
        
        try:
            response_stream = model.generate_content(messages, stream=True, **request_params)
            
            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content:
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            # Text content
                            yield {
                                "id": f"gemini_{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model_name,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": part.text},
                                    "finish_reason": None
                                }]
                            }
                        elif hasattr(part, 'function_call') and part.function_call:
                            # Function call
                            func_call = part.function_call
                            yield {
                                "id": f"gemini_{int(time.time())}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model_name,
                                "choices": [{
                                    "index": 0,
                                    "delta": {
                                        "tool_calls": [{
                                            "index": 0,
                                            "id": f"call_{hash(func_call.name)}",
                                            "type": "function",
                                            "function": {
                                                "name": func_call.name,
                                                "arguments": json.dumps(dict(func_call.args))
                                            }
                                        }]
                                    },
                                    "finish_reason": None
                                }]
                            }
                            
        except Exception as e:
            logger.error(f"[Gemini] stream response error: {e}")
            yield {
                "error": True,
                "message": str(e),
                "status_code": 500
            }
