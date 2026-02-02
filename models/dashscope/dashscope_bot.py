# encoding:utf-8

import json
from models.bot import Bot
from models.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf, load_config
from .dashscope_session import DashscopeSession
import os
import dashscope
from http import HTTPStatus



dashscope_models = {
    "qwen-turbo": dashscope.Generation.Models.qwen_turbo,
    "qwen-plus": dashscope.Generation.Models.qwen_plus,
    "qwen-max": dashscope.Generation.Models.qwen_max,
    "qwen-bailian-v1": dashscope.Generation.Models.bailian_v1,
    # Qwen3 series models - use string directly as model name
    "qwen3-max": "qwen3-max",
    "qwen3-plus": "qwen3-plus", 
    "qwen3-turbo": "qwen3-turbo",
    # Other new models
    "qwen-long": "qwen-long",
    "qwq-32b-preview": "qwq-32b-preview",
    "qvq-72b-preview": "qvq-72b-preview"
}
# ZhipuAI对话模型API
class DashscopeBot(Bot):
    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(DashscopeSession, model=conf().get("model") or "qwen-plus")
        self.model_name = conf().get("model") or "qwen-plus"
        self.api_key = conf().get("dashscope_api_key")
        if self.api_key:
            os.environ["DASHSCOPE_API_KEY"] = self.api_key
        self.client = dashscope.Generation

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info("[DASHSCOPE] query={}".format(query))

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
            logger.debug("[DASHSCOPE] session query={}".format(session.messages))

            reply_content = self.reply_text(session)
            logger.debug(
                "[DASHSCOPE] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
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
                logger.debug("[DASHSCOPE] reply {} used 0 tokens.".format(reply_content))
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: DashscopeSession, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            dashscope.api_key = self.api_key
            response = self.client.call(
                dashscope_models[self.model_name],
                messages=session.messages,
                result_format="message"
            )
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0]["message"]["content"]
                return {
                    "total_tokens": response.usage["total_tokens"],
                    "completion_tokens": response.usage["output_tokens"],
                    "content": content,
                }
            else:
                logger.error('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                    response.request_id, response.status_code,
                    response.code, response.message
                ))
                result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
                need_retry = retry_count < 2
                result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
                if need_retry:
                    return self.reply_text(session, retry_count + 1)
                else:
                    return result
        except Exception as e:
            logger.exception(e)
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if need_retry:
                return self.reply_text(session, retry_count + 1)
            else:
                return result

    def call_with_tools(self, messages, tools=None, stream=False, **kwargs):
        """
        Call DashScope API with tool support for agent integration
        
        This method handles:
        1. Format conversion (Claude format → DashScope format)
        2. System prompt injection
        3. API calling with DashScope SDK
        4. Thinking mode support (enable_thinking for Qwen3)
        
        Args:
            messages: List of messages (may be in Claude format from agent)
            tools: List of tool definitions (may be in Claude format from agent)
            stream: Whether to use streaming
            **kwargs: Additional parameters (max_tokens, temperature, system, etc.)
            
        Returns:
            Formatted response or generator for streaming
        """
        try:
            # Convert messages from Claude format to DashScope format
            messages = self._convert_messages_to_dashscope_format(messages)
            
            # Convert tools from Claude format to DashScope format
            if tools:
                tools = self._convert_tools_to_dashscope_format(tools)
            
            # Handle system prompt
            system_prompt = kwargs.get('system')
            if system_prompt:
                # Add system message at the beginning if not already present
                if not messages or messages[0].get('role') != 'system':
                    messages = [{"role": "system", "content": system_prompt}] + messages
                else:
                    # Replace existing system message
                    messages[0] = {"role": "system", "content": system_prompt}
            
            # Build request parameters
            model_name = kwargs.get("model", self.model_name)
            
            parameters = {
                "result_format": "message",  # Required for tool calling
                "temperature": kwargs.get("temperature", conf().get("temperature", 0.85)),
                "top_p": kwargs.get("top_p", conf().get("top_p", 0.8)),
            }
            
            # Add max_tokens if specified
            if kwargs.get("max_tokens"):
                parameters["max_tokens"] = kwargs["max_tokens"]
            
            # Add tools if provided
            if tools:
                parameters["tools"] = tools
                # Add tool_choice if specified
                if kwargs.get("tool_choice"):
                    parameters["tool_choice"] = kwargs["tool_choice"]
            
            # Add thinking parameters for Qwen3 models (disabled by default for stability)
            if "qwen3" in model_name.lower() or "qwq" in model_name.lower():
                # Only enable thinking mode if explicitly requested
                enable_thinking = kwargs.get("enable_thinking", False)
                if enable_thinking:
                    parameters["enable_thinking"] = True
                    
                    # Set thinking budget if specified
                    if kwargs.get("thinking_budget"):
                        parameters["thinking_budget"] = kwargs["thinking_budget"]
                    
                    # Qwen3 requires incremental_output=true in thinking mode
                    if stream:
                        parameters["incremental_output"] = True
            
            # Always use incremental_output for streaming (for better token-by-token streaming)
            # This is especially important for tool calling to avoid incomplete responses
            if stream:
                parameters["incremental_output"] = True
            
            # Make API call with DashScope SDK
            if stream:
                return self._handle_stream_response(model_name, messages, parameters)
            else:
                return self._handle_sync_response(model_name, messages, parameters)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[DASHSCOPE] call_with_tools error: {error_msg}")
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
    
    def _handle_sync_response(self, model_name, messages, parameters):
        """Handle synchronous DashScope API response"""
        try:
            # Set API key before calling
            dashscope.api_key = self.api_key
            
            response = dashscope.Generation.call(
                model=dashscope_models.get(model_name, model_name),
                messages=messages,
                **parameters
            )
            
            if response.status_code == HTTPStatus.OK:
                # Convert DashScope response to OpenAI-compatible format
                choice = response.output.choices[0]
                return {
                    "id": response.request_id,
                    "object": "chat.completion",
                    "created": 0,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content,
                            "tool_calls": self._convert_tool_calls_to_openai_format(
                                choice.message.get("tool_calls")
                            )
                        },
                        "finish_reason": choice.finish_reason
                    }],
                    "usage": {
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            else:
                logger.error(f"[DASHSCOPE] API error: {response.code} - {response.message}")
                return {
                    "error": True,
                    "message": response.message,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"[DASHSCOPE] sync response error: {e}")
            return {
                "error": True,
                "message": str(e),
                "status_code": 500
            }
    
    def _handle_stream_response(self, model_name, messages, parameters):
        """Handle streaming DashScope API response"""
        try:
            # Set API key before calling
            dashscope.api_key = self.api_key
            
            responses = dashscope.Generation.call(
                model=dashscope_models.get(model_name, model_name),
                messages=messages,
                stream=True,
                **parameters
            )
            
            # Stream chunks to caller, converting to OpenAI format
            for response in responses:
                if response.status_code != HTTPStatus.OK:
                    logger.error(f"[DASHSCOPE] Stream error: {response.code} - {response.message}")
                    yield {
                        "error": True,
                        "message": response.message,
                        "status_code": response.status_code
                    }
                    continue
                
                # Get choice - use try-except because DashScope raises KeyError on hasattr()
                try:
                    if isinstance(response.output, dict):
                        choice = response.output['choices'][0]
                    else:
                        choice = response.output.choices[0]
                except (KeyError, AttributeError, IndexError) as e:
                    logger.warning(f"[DASHSCOPE] Cannot get choice: {e}")
                    continue
                
                # Get finish_reason safely
                finish_reason = None
                try:
                    if isinstance(choice, dict):
                        finish_reason = choice.get('finish_reason')
                    else:
                        finish_reason = choice.finish_reason
                except (KeyError, AttributeError):
                    pass
                
                # Convert to OpenAI-compatible format
                openai_chunk = {
                    "id": response.request_id,
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": model_name,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": finish_reason
                    }]
                }
                
                # Get message safely - use try-except
                message = {}
                try:
                    if isinstance(choice, dict):
                        message = choice.get('message', {})
                    else:
                        message = choice.message
                except (KeyError, AttributeError):
                    pass
                
                # Add role if present
                role = None
                try:
                    if isinstance(message, dict):
                        role = message.get('role')
                    else:
                        role = message.role
                except (KeyError, AttributeError):
                    pass
                if role:
                    openai_chunk["choices"][0]["delta"]["role"] = role
                
                # Add content if present
                content = None
                try:
                    if isinstance(message, dict):
                        content = message.get('content')
                    else:
                        content = message.content
                except (KeyError, AttributeError):
                    pass
                if content:
                    openai_chunk["choices"][0]["delta"]["content"] = content
                
                # Add tool_calls if present
                # DashScope's response object raises KeyError on hasattr() if attr doesn't exist
                # So we use try-except instead
                tool_calls = None
                try:
                    if isinstance(message, dict):
                        tool_calls = message.get('tool_calls')
                    else:
                        tool_calls = message.tool_calls
                except (KeyError, AttributeError):
                    pass
                
                if tool_calls:
                    openai_chunk["choices"][0]["delta"]["tool_calls"] = self._convert_tool_calls_to_openai_format(tool_calls)
                
                yield openai_chunk
                
        except Exception as e:
            logger.error(f"[DASHSCOPE] stream response error: {e}")
            yield {
                "error": True,
                "message": str(e),
                "status_code": 500
            }
    
    def _convert_tools_to_dashscope_format(self, tools):
        """
        Convert tools from Claude format to DashScope format
        
        Claude format: {name, description, input_schema}
        DashScope format: {type: "function", function: {name, description, parameters}}
        """
        if not tools:
            return None
        
        dashscope_tools = []
        for tool in tools:
            # Check if already in DashScope/OpenAI format
            if 'type' in tool and tool['type'] == 'function':
                dashscope_tools.append(tool)
            else:
                # Convert from Claude format
                dashscope_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "parameters": tool.get("input_schema", {})
                    }
                })
        
        return dashscope_tools
    
    def _convert_messages_to_dashscope_format(self, messages):
        """
        Convert messages from Claude format to DashScope format
        
        Claude uses content blocks with types like 'tool_use', 'tool_result'
        DashScope uses 'tool_calls' in assistant messages and 'tool' role for results
        """
        if not messages:
            return []
        
        dashscope_messages = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # Handle string content (already in correct format)
            if isinstance(content, str):
                dashscope_messages.append(msg)
                continue
            
            # Handle list content (Claude format with content blocks)
            if isinstance(content, list):
                # Check if this is a tool result message (user role with tool_result blocks)
                if role == "user" and any(block.get("type") == "tool_result" for block in content):
                    # Convert each tool_result block to a separate tool message
                    for block in content:
                        if block.get("type") == "tool_result":
                            dashscope_messages.append({
                                "role": "tool",
                                "content": block.get("content", ""),
                                "tool_call_id": block.get("tool_use_id")  # DashScope uses 'tool_call_id'
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
                    
                    # Build DashScope format assistant message
                    dashscope_msg = {
                        "role": "assistant"
                    }
                    
                    # Add content only if there is actual text
                    # DashScope API: when tool_calls exist, content should be None or omitted if empty
                    if text_parts:
                        dashscope_msg["content"] = " ".join(text_parts)
                    elif not tool_calls:
                        # If no tool_calls and no text, set empty string (rare case)
                        dashscope_msg["content"] = ""
                    # If there are tool_calls but no text, don't set content field at all
                    
                    if tool_calls:
                        dashscope_msg["tool_calls"] = tool_calls
                    
                    dashscope_messages.append(dashscope_msg)
                else:
                    # Other list content, keep as is
                    dashscope_messages.append(msg)
            else:
                # Other formats, keep as is
                dashscope_messages.append(msg)
        
        return dashscope_messages
    
    def _convert_tool_calls_to_openai_format(self, tool_calls):
        """Convert DashScope tool_calls to OpenAI format"""
        if not tool_calls:
            return None
        
        openai_tool_calls = []
        for tool_call in tool_calls:
            # DashScope format is already similar to OpenAI
            if isinstance(tool_call, dict):
                openai_tool_calls.append(tool_call)
            else:
                # Handle object format
                openai_tool_calls.append({
                    "id": getattr(tool_call, 'id', None),
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
        
        return openai_tool_calls
