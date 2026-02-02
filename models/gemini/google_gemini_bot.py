"""
Google gemini bot

@author zhayujie
@Date 2023/12/15
"""
# encoding:utf-8

import json
import time
import requests
from models.bot import Bot
import google.generativeai as genai
from models.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from models.chatgpt.chat_gpt_session import ChatGPTSession
from models.baidu.baidu_wenxin_session import BaiduWenxinSession
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
        
        # 支持自定义API base地址
        self.api_base = conf().get("gemini_api_base", "").strip()
        if self.api_base:
            # 移除末尾的斜杠
            self.api_base = self.api_base.rstrip('/')
            logger.info(f"[Gemini] Using custom API base: {self.api_base}")
        else:
            self.api_base = "https://generativelanguage.googleapis.com"

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
        Call Gemini API with tool support using REST API (following official docs)
        
        Args:
            messages: List of messages (OpenAI format)
            tools: List of tool definitions (OpenAI/Claude format)
            stream: Whether to use streaming
            **kwargs: Additional parameters (system, max_tokens, temperature, etc.)
            
        Returns:
            Formatted response compatible with OpenAI format or generator for streaming
        """
        try:
            model_name = kwargs.get("model", self.model or "gemini-1.5-flash")
            
            # Build REST API payload
            payload = {"contents": []}
            
            # Extract and set system instruction
            system_prompt = kwargs.get("system", "")
            if not system_prompt:
                for msg in messages:
                    if msg.get("role") == "system":
                        system_prompt = msg["content"]
                        break
            
            if system_prompt:
                payload["system_instruction"] = {
                    "parts": [{"text": system_prompt}]
                }
            
            # Convert messages to Gemini format
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")
                
                if role == "system":
                    continue
                
                # Convert role
                gemini_role = "user" if role in ["user", "tool"] else "model"
                
                # Handle different content formats
                parts = []
                
                if isinstance(content, str):
                    # Simple text content
                    parts.append({"text": content})
                    
                elif isinstance(content, list):
                    # List of content blocks (Claude format)
                    for block in content:
                        if not isinstance(block, dict):
                            if isinstance(block, str):
                                parts.append({"text": block})
                            continue
                        
                        block_type = block.get("type")
                        
                        if block_type == "text":
                            # Text block
                            parts.append({"text": block.get("text", "")})
                            
                        elif block_type == "tool_result":
                            # Convert Claude tool_result to Gemini functionResponse
                            tool_use_id = block.get("tool_use_id")
                            tool_content = block.get("content", "")
                            
                            # Try to parse tool content as JSON
                            try:
                                if isinstance(tool_content, str):
                                    tool_result_data = json.loads(tool_content)
                                else:
                                    tool_result_data = tool_content
                            except:
                                tool_result_data = {"result": tool_content}
                            
                            # Find the tool name from previous messages
                            # Look for the corresponding tool_call in model's message
                            tool_name = None
                            for prev_msg in reversed(messages):
                                if prev_msg.get("role") == "assistant":
                                    prev_content = prev_msg.get("content", [])
                                    if isinstance(prev_content, list):
                                        for prev_block in prev_content:
                                            if isinstance(prev_block, dict) and prev_block.get("type") == "tool_use":
                                                if prev_block.get("id") == tool_use_id:
                                                    tool_name = prev_block.get("name")
                                                    break
                                    if tool_name:
                                        break
                            
                            # Gemini functionResponse format
                            parts.append({
                                "functionResponse": {
                                    "name": tool_name or "unknown",
                                    "response": tool_result_data
                                }
                            })
                            
                        elif "text" in block:
                            # Generic text field
                            parts.append({"text": block["text"]})
                
                if parts:
                    payload["contents"].append({
                        "role": gemini_role,
                        "parts": parts
                    })
            
            # Generation config
            gen_config = {}
            if kwargs.get("temperature") is not None:
                gen_config["temperature"] = kwargs["temperature"]

            if gen_config:
                payload["generationConfig"] = gen_config
            
            # Convert tools to Gemini format (REST API style)
            if tools:
                gemini_tools = self._convert_tools_to_gemini_rest_format(tools)
                if gemini_tools:
                    payload["tools"] = gemini_tools
            
            # Make REST API call
            base_url = f"{self.api_base}/v1beta"
            endpoint = f"{base_url}/models/{model_name}:generateContent"
            if stream:
                endpoint = f"{base_url}/models/{model_name}:streamGenerateContent?alt=sse"
            
            headers = {
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                stream=stream,
                timeout=60
            )
            
            # Check HTTP status for stream mode (for non-stream, it's checked in handler)
            if stream and response.status_code != 200:
                error_text = response.text
                logger.error(f"[Gemini] API error ({response.status_code}): {error_text}")
                def error_generator():
                    yield {
                        "error": True,
                        "message": f"Gemini API error: {error_text}",
                        "status_code": response.status_code
                    }
                return error_generator()
            
            if stream:
                return self._handle_gemini_rest_stream_response(response, model_name)
            else:
                return self._handle_gemini_rest_sync_response(response, model_name)
                
        except Exception as e:
            logger.error(f"[Gemini] call_with_tools error: {e}", exc_info=True)
            error_msg = str(e)  # Capture error message before creating generator
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
                    "message": str(e),
                    "status_code": 500
                }
    
    def _convert_tools_to_gemini_rest_format(self, tools_list):
        """
        Convert tools to Gemini REST API format
        
        Handles both OpenAI and Claude/Agent formats.
        Returns: [{"functionDeclarations": [...]}]
        """
        function_declarations = []
        
        for tool in tools_list:
            # Extract name, description, and parameters based on format
            if tool.get("type") == "function":
                # OpenAI format: {"type": "function", "function": {...}}
                func = tool.get("function", {})
                name = func.get("name")
                description = func.get("description", "")
                parameters = func.get("parameters", {})
            else:
                # Claude/Agent format: {"name": "...", "description": "...", "input_schema": {...}}
                name = tool.get("name")
                description = tool.get("description", "")
                parameters = tool.get("input_schema", {})
            
            if not name:
                logger.warning(f"[Gemini] Skipping tool without name: {tool}")
                continue
            
            function_declarations.append({
                "name": name,
                "description": description,
                "parameters": parameters
            })
        
        # All functionDeclarations must be in a single tools object (per Gemini REST API spec)
        return [{
            "functionDeclarations": function_declarations
        }] if function_declarations else []
    
    def _handle_gemini_rest_sync_response(self, response, model_name):
        """Handle Gemini REST API sync response and convert to OpenAI format"""
        try:
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"[Gemini] API error ({response.status_code}): {error_text}")
                return {
                    "error": True,
                    "message": f"Gemini API error: {error_text}",
                    "status_code": response.status_code
                }
            
            data = response.json()
            logger.debug(f"[Gemini] Response data: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            # Extract from Gemini response format
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning("[Gemini] No candidates in response")
                return {
                    "error": True,
                    "message": "No candidates in response",
                    "status_code": 500
                }
            
            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])
            
            logger.debug(f"[Gemini] Candidate parts count: {len(parts)}")
            
            # Extract text and function calls
            text_content = ""
            tool_calls = []
            
            for part in parts:
                # Check for text
                if "text" in part:
                    text_content += part["text"]
                    logger.debug(f"[Gemini] Text part: {part['text'][:100]}...")
                
                # Check for functionCall (per REST API docs)
                if "functionCall" in part:
                    fc = part["functionCall"]
                    logger.info(f"[Gemini] Function call detected: {fc.get('name')}")
                    
                    tool_calls.append({
                        "id": f"call_{int(time.time() * 1000000)}",
                        "type": "function",
                        "function": {
                            "name": fc.get("name"),
                            "arguments": json.dumps(fc.get("args", {}))
                        }
                    })
            
            logger.info(f"[Gemini] Response: text={len(text_content)} chars, tool_calls={len(tool_calls)}")
            
            # Build OpenAI format response
            message_dict = {
                "role": "assistant",
                "content": text_content or None
            }
            if tool_calls:
                message_dict["tool_calls"] = tool_calls
            
            return {
                "id": f"chatcmpl-{time.time()}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "message": message_dict,
                    "finish_reason": "tool_calls" if tool_calls else "stop"
                }],
                "usage": data.get("usageMetadata", {})
            }
            
        except Exception as e:
            logger.error(f"[Gemini] sync response error: {e}", exc_info=True)
            return {
                "error": True,
                "message": str(e),
                "status_code": 500
            }
    
    def _handle_gemini_rest_stream_response(self, response, model_name):
        """Handle Gemini REST API stream response"""
        try:
            all_tool_calls = []
            has_sent_tool_calls = False
            has_content = False  # Track if any content was sent
            chunk_count = 0
            last_finish_reason = None
            last_safety_ratings = None
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8')
                
                # Skip SSE prefixes
                if line.startswith('data: '):
                    line = line[6:]
                
                if not line or line == '[DONE]':
                    continue
                
                try:
                    chunk_data = json.loads(line)
                    chunk_count += 1
                    
                    candidates = chunk_data.get("candidates", [])
                    if not candidates:
                        logger.debug("[Gemini] No candidates in chunk")
                        continue
                    
                    candidate = candidates[0]
                    
                    # 记录 finish_reason 和 safety_ratings
                    if "finishReason" in candidate:
                        last_finish_reason = candidate["finishReason"]
                    if "safetyRatings" in candidate:
                        last_safety_ratings = candidate["safetyRatings"]
                    
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])
                    
                    if not parts:
                        logger.debug("[Gemini] No parts in candidate content")
                    
                    # Stream text content
                    for part in parts:
                        if "text" in part and part["text"]:
                            has_content = True
                            yield {
                                "id": f"chatcmpl-{time.time()}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model_name,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": part["text"]},
                                    "finish_reason": None
                                }]
                            }
                        
                        # Collect function calls
                        if "functionCall" in part:
                            fc = part["functionCall"]
                            logger.info(f"[Gemini] Function call: {fc.get('name')}")
                            all_tool_calls.append({
                                "index": len(all_tool_calls),  # Add index to differentiate multiple tool calls
                                "id": f"call_{int(time.time() * 1000000)}_{len(all_tool_calls)}",
                                "type": "function",
                                "function": {
                                    "name": fc.get("name"),
                                    "arguments": json.dumps(fc.get("args", {}))
                                }
                            })
                    
                except json.JSONDecodeError as je:
                    logger.debug(f"[Gemini] JSON decode error: {je}")
                    continue
            
            # Send tool calls if any were collected
            if all_tool_calls and not has_sent_tool_calls:
                yield {
                    "id": f"chatcmpl-{time.time()}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {"tool_calls": all_tool_calls},
                        "finish_reason": None
                    }]
                }
                has_sent_tool_calls = True
            
            # 如果返回空响应，记录详细警告
            if not has_content and not all_tool_calls:
                logger.warning(f"[Gemini] ⚠️  Empty response detected!")
            
            # Final chunk
            yield {
                "id": f"chatcmpl-{time.time()}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "tool_calls" if all_tool_calls else "stop"
                }]
            }
                    
        except Exception as e:
            logger.error(f"[Gemini] stream response error: {e}", exc_info=True)
            error_msg = str(e)
            yield {
                "error": True,
                "message": error_msg,
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
