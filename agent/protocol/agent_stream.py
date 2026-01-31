"""
Agent Stream Execution Module - Multi-turn reasoning based on tool-call

Provides streaming output, event system, and complete tool-call loop
"""
import json
import time
from typing import List, Dict, Any, Optional, Callable

from common.log import logger
from agent.protocol.models import LLMRequest, LLMModel
from agent.tools.base_tool import BaseTool, ToolResult


class AgentStreamExecutor:
    """
    Agent Stream Executor
    
    Handles multi-turn reasoning loop based on tool-call:
    1. LLM generates response (may include tool calls)
    2. Execute tools
    3. Return results to LLM
    4. Repeat until no more tool calls
    """

    def __init__(
            self,
            agent,  # Agent instance
            model: LLMModel,
            system_prompt: str,
            tools: List[BaseTool],
            max_turns: int = 50,
            on_event: Optional[Callable] = None,
            messages: Optional[List[Dict]] = None
    ):
        """
        Initialize stream executor
        
        Args:
            agent: Agent instance (for accessing context)
            model: LLM model
            system_prompt: System prompt
            tools: List of available tools
            max_turns: Maximum number of turns
            on_event: Event callback function
            messages: Optional existing message history (for persistent conversations)
        """
        self.agent = agent
        self.model = model
        self.system_prompt = system_prompt
        # Convert tools list to dict
        self.tools = {tool.name: tool for tool in tools} if isinstance(tools, list) else tools
        self.max_turns = max_turns
        self.on_event = on_event

        # Message history - use provided messages or create new list
        self.messages = messages if messages is not None else []

    def _emit_event(self, event_type: str, data: dict = None):
        """Emit event"""
        if self.on_event:
            try:
                self.on_event({
                    "type": event_type,
                    "timestamp": time.time(),
                    "data": data or {}
                })
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    def run_stream(self, user_message: str) -> str:
        """
        Execute streaming reasoning loop
        
        Args:
            user_message: User message
            
        Returns:
            Final response text
        """
        # Log user message with model info
        logger.info(f"{'='*50}")
        logger.info(f"🤖 Model: {self.model.model}")
        logger.info(f"👤 用户: {user_message}")
        logger.info(f"{'='*50}")
        
        # Add user message (Claude format - use content blocks for consistency)
        self.messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_message
                }
            ]
        })

        self._emit_event("agent_start")

        final_response = ""
        turn = 0

        try:
            while turn < self.max_turns:
                turn += 1
                logger.info(f"第 {turn} 轮")
                self._emit_event("turn_start", {"turn": turn})

                # Check if memory flush is needed (before calling LLM)
                if self.agent.memory_manager and hasattr(self.agent, 'last_usage'):
                    usage = self.agent.last_usage
                    if usage and 'input_tokens' in usage:
                        current_tokens = usage.get('input_tokens', 0)
                        context_window = self.agent._get_model_context_window()
                        # Use configured reserve_tokens or calculate based on context window
                        reserve_tokens = self.agent._get_context_reserve_tokens()
                        # Use smaller soft_threshold to trigger flush earlier (e.g., at 50K tokens)
                        soft_threshold = 10000  # Trigger 10K tokens before limit

                        if self.agent.memory_manager.should_flush_memory(
                                current_tokens=current_tokens,
                                context_window=context_window,
                                reserve_tokens=reserve_tokens,
                                soft_threshold=soft_threshold
                        ):
                            self._emit_event("memory_flush_start", {
                                "current_tokens": current_tokens,
                                "threshold": context_window - reserve_tokens - soft_threshold
                            })

                            # TODO: Execute memory flush in background
                            # This would require async support
                            logger.info(f"Memory flush recommended at {current_tokens} tokens")

                # Call LLM
                assistant_msg, tool_calls = self._call_llm_stream()
                final_response = assistant_msg

                # No tool calls, end loop
                if not tool_calls:
                    # 检查是否返回了空响应
                    if not assistant_msg:
                        logger.warning(f"[Agent] LLM returned empty response (no content and no tool calls)")
                        
                        # 生成通用的友好提示
                        final_response = (
                            "抱歉，我暂时无法生成回复。请尝试换一种方式描述你的需求，或稍后再试。"
                        )
                        logger.info(f"Generated fallback response for empty LLM output")
                    else:
                        logger.info(f"💭 {assistant_msg[:150]}{'...' if len(assistant_msg) > 150 else ''}")
                    
                    logger.info(f"✅ 完成 (无工具调用)")
                    self._emit_event("turn_end", {
                        "turn": turn,
                        "has_tool_calls": False
                    })
                    break

                # Log tool calls with arguments
                tool_calls_str = []
                for tc in tool_calls:
                    args_str = ', '.join([f"{k}={v}" for k, v in tc['arguments'].items()])
                    if args_str:
                        tool_calls_str.append(f"{tc['name']}({args_str})")
                    else:
                        tool_calls_str.append(tc['name'])
                logger.info(f"🔧 {', '.join(tool_calls_str)}")

                # Execute tools
                tool_results = []
                tool_result_blocks = []

                for tool_call in tool_calls:
                    result = self._execute_tool(tool_call)
                    tool_results.append(result)
                    
                    # Log tool result in compact format
                    status_emoji = "✅" if result.get("status") == "success" else "❌"
                    result_data = result.get('result', '')
                    # Format result string with proper Chinese character support
                    if isinstance(result_data, (dict, list)):
                        result_str = json.dumps(result_data, ensure_ascii=False)
                    else:
                        result_str = str(result_data)
                    logger.info(f"  {status_emoji} {tool_call['name']} ({result.get('execution_time', 0):.2f}s): {result_str[:200]}{'...' if len(result_str) > 200 else ''}")

                    # Build tool result block (Claude format)
                    # Format content in a way that's easy for LLM to understand
                    is_error = result.get("status") == "error"
                    
                    if is_error:
                        # For errors, provide clear error message
                        result_content = f"Error: {result.get('result', 'Unknown error')}"
                    elif isinstance(result.get('result'), dict):
                        # For dict results, use JSON format
                        result_content = json.dumps(result.get('result'), ensure_ascii=False)
                    elif isinstance(result.get('result'), str):
                        # For string results, use directly
                        result_content = result.get('result')
                    else:
                        # Fallback to full JSON
                        result_content = json.dumps(result, ensure_ascii=False)
                    
                    tool_result_block = {
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result_content
                    }
                    
                    # Add is_error field for Claude API (helps model understand failures)
                    if is_error:
                        tool_result_block["is_error"] = True
                    
                    tool_result_blocks.append(tool_result_block)

                # Add tool results to message history as user message (Claude format)
                self.messages.append({
                    "role": "user",
                    "content": tool_result_blocks
                })

                self._emit_event("turn_end", {
                    "turn": turn,
                    "has_tool_calls": True,
                    "tool_count": len(tool_calls)
                })

            if turn >= self.max_turns:
                logger.warning(f"⚠️  已达到最大轮数限制: {self.max_turns}")
                if not final_response:
                    final_response = (
                        "抱歉，我在处理你的请求时遇到了一些困难，尝试了多次仍未能完成。"
                        "请尝试简化你的问题，或换一种方式描述。"
                    )

        except Exception as e:
            logger.error(f"❌ Agent执行错误: {e}")
            self._emit_event("error", {"error": str(e)})
            raise

        finally:
            logger.info(f"🏁 完成({turn}轮)")
            self._emit_event("agent_end", {"final_response": final_response})

        return final_response

    def _call_llm_stream(self, retry_on_empty=True, retry_count=0, max_retries=3) -> tuple[str, List[Dict]]:
        """
        Call LLM with streaming and automatic retry on errors
        
        Args:
            retry_on_empty: Whether to retry once if empty response is received
            retry_count: Current retry attempt (internal use)
            max_retries: Maximum number of retries for API errors
        
        Returns:
            (response_text, tool_calls)
        """
        # Trim messages if needed (using agent's context management)
        self._trim_messages()

        # Prepare messages
        messages = self._prepare_messages()
        
        # Debug: log message structure
        logger.debug(f"Sending {len(messages)} messages to LLM")
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, list):
                content_types = [c.get("type") for c in content if isinstance(c, dict)]
                logger.debug(f"  Message {i}: role={role}, content_blocks={content_types}")
            else:
                logger.debug(f"  Message {i}: role={role}, content_length={len(str(content))}")

        # Prepare tool definitions (OpenAI/Claude format)
        tools_schema = None
        if self.tools:
            tools_schema = []
            for tool in self.tools.values():
                tools_schema.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.params  # Claude uses input_schema
                })

        # Create request
        request = LLMRequest(
            messages=messages,
            temperature=0,
            stream=True,
            tools=tools_schema,
            system=self.system_prompt  # Pass system prompt separately for Claude API
        )

        self._emit_event("message_start", {"role": "assistant"})

        # Streaming response
        full_content = ""
        tool_calls_buffer = {}  # {index: {id, name, arguments}}

        try:
            stream = self.model.call_stream(request)

            for chunk in stream:
                # Check for errors
                if isinstance(chunk, dict) and chunk.get("error"):
                    # Extract error message from nested structure
                    error_data = chunk.get("error", {})
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", chunk.get("message", "Unknown error"))
                        error_code = error_data.get("code", "")
                    else:
                        error_msg = chunk.get("message", str(error_data))
                        error_code = ""
                    
                    status_code = chunk.get("status_code", "N/A")
                    logger.error(f"API Error: {error_msg} (Status: {status_code}, Code: {error_code})")
                    logger.error(f"Full error chunk: {chunk}")
                    
                    # Raise exception with full error message for retry logic
                    raise Exception(f"{error_msg} (Status: {status_code})")

                # Parse chunk
                if isinstance(chunk, dict) and "choices" in chunk:
                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})

                    # Handle text content
                    if "content" in delta and delta["content"]:
                        content_delta = delta["content"]
                        full_content += content_delta
                        self._emit_event("message_update", {"delta": content_delta})

                    # Handle tool calls
                    if "tool_calls" in delta:
                        for tc_delta in delta["tool_calls"]:
                            index = tc_delta.get("index", 0)

                            if index not in tool_calls_buffer:
                                tool_calls_buffer[index] = {
                                    "id": "",
                                    "name": "",
                                    "arguments": ""
                                }

                            if "id" in tc_delta:
                                tool_calls_buffer[index]["id"] = tc_delta["id"]

                            if "function" in tc_delta:
                                func = tc_delta["function"]
                                if "name" in func:
                                    tool_calls_buffer[index]["name"] = func["name"]
                                if "arguments" in func:
                                    tool_calls_buffer[index]["arguments"] += func["arguments"]

        except Exception as e:
            error_str = str(e).lower()
            # Check if error is retryable (timeout, connection, rate limit, server busy, etc.)
            is_retryable = any(keyword in error_str for keyword in [
                'timeout', 'timed out', 'connection', 'network', 
                'rate limit', 'overloaded', 'unavailable', 'busy', 'retry',
                '429', '500', '502', '503', '504', '512'
            ])
            
            if is_retryable and retry_count < max_retries:
                wait_time = (retry_count + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                logger.warning(f"⚠️ LLM API error (attempt {retry_count + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self._call_llm_stream(
                    retry_on_empty=retry_on_empty, 
                    retry_count=retry_count + 1,
                    max_retries=max_retries
                )
            else:
                if retry_count >= max_retries:
                    logger.error(f"❌ LLM API error after {max_retries} retries: {e}")
                else:
                    logger.error(f"❌ LLM call error (non-retryable): {e}")
                raise

        # Parse tool calls
        tool_calls = []
        for idx in sorted(tool_calls_buffer.keys()):
            tc = tool_calls_buffer[idx]
            try:
                arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool arguments: {tc['arguments']}")
                arguments = {}

            tool_calls.append({
                "id": tc["id"],
                "name": tc["name"],
                "arguments": arguments
            })

        # Check for empty response and retry once if enabled
        if retry_on_empty and not full_content and not tool_calls:
            logger.warning(f"⚠️  LLM returned empty response, retrying once...")
            self._emit_event("message_end", {
                "content": "",
                "tool_calls": [],
                "empty_retry": True
            })
            # Retry without retry flag to avoid infinite loop
            return self._call_llm_stream(
                retry_on_empty=False, 
                retry_count=retry_count,
                max_retries=max_retries
            )

        # Add assistant message to history (Claude format uses content blocks)
        assistant_msg = {"role": "assistant", "content": []}

        # Add text content block if present
        if full_content:
            assistant_msg["content"].append({
                "type": "text",
                "text": full_content
            })

        # Add tool_use blocks if present
        if tool_calls:
            for tc in tool_calls:
                assistant_msg["content"].append({
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["arguments"]
                })
        
        # Only append if content is not empty
        if assistant_msg["content"]:
            self.messages.append(assistant_msg)

        self._emit_event("message_end", {
            "content": full_content,
            "tool_calls": tool_calls
        })

        return full_content, tool_calls

    def _execute_tool(self, tool_call: Dict) -> Dict[str, Any]:
        """
        Execute tool
        
        Args:
            tool_call: {"id": str, "name": str, "arguments": dict}
            
        Returns:
            Tool execution result
        """
        tool_name = tool_call["name"]
        tool_id = tool_call["id"]
        arguments = tool_call["arguments"]

        self._emit_event("tool_execution_start", {
            "tool_call_id": tool_id,
            "tool_name": tool_name,
            "arguments": arguments
        })

        try:
            tool = self.tools.get(tool_name)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found")

            # Set tool context
            tool.model = self.model
            tool.context = self.agent

            # Execute tool
            start_time = time.time()
            result: ToolResult = tool.execute_tool(arguments)
            execution_time = time.time() - start_time

            result_dict = {
                "status": result.status,
                "result": result.result,
                "execution_time": execution_time
            }

            # Auto-refresh skills after skill creation
            if tool_name == "bash" and result.status == "success":
                command = arguments.get("command", "")
                if "init_skill.py" in command and self.agent.skill_manager:
                    logger.info("Detected skill creation, refreshing skills...")
                    self.agent.refresh_skills()
                    logger.info(f"Skills refreshed! Now have {len(self.agent.skill_manager.skills)} skills")

            self._emit_event("tool_execution_end", {
                "tool_call_id": tool_id,
                "tool_name": tool_name,
                **result_dict
            })

            return result_dict

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            error_result = {
                "status": "error",
                "result": str(e),
                "execution_time": 0
            }
            self._emit_event("tool_execution_end", {
                "tool_call_id": tool_id,
                "tool_name": tool_name,
                **error_result
            })
            return error_result

    def _trim_messages(self):
        """
        Trim message history to stay within context limits.
        Uses agent's context management configuration.
        """
        if not self.messages or not self.agent:
            return

        # Get context window and reserve tokens from agent
        context_window = self.agent._get_model_context_window()
        reserve_tokens = self.agent._get_context_reserve_tokens()
        max_tokens = context_window - reserve_tokens

        # Estimate current tokens
        current_tokens = sum(self.agent._estimate_message_tokens(msg) for msg in self.messages)

        # Add system prompt tokens
        system_tokens = self.agent._estimate_message_tokens({"role": "system", "content": self.system_prompt})
        current_tokens += system_tokens

        # If under limit, no need to trim
        if current_tokens <= max_tokens:
            return

        # Keep messages from newest, accumulating tokens
        available_tokens = max_tokens - system_tokens
        kept_messages = []
        accumulated_tokens = 0

        for msg in reversed(self.messages):
            msg_tokens = self.agent._estimate_message_tokens(msg)
            if accumulated_tokens + msg_tokens <= available_tokens:
                kept_messages.insert(0, msg)
                accumulated_tokens += msg_tokens
            else:
                break

        old_count = len(self.messages)
        self.messages = kept_messages
        new_count = len(self.messages)

        if old_count > new_count:
            logger.info(
                f"Context trimmed: {old_count} -> {new_count} messages "
                f"(~{current_tokens} -> ~{system_tokens + accumulated_tokens} tokens, "
                f"limit: {max_tokens})"
            )

    def _prepare_messages(self) -> List[Dict[str, Any]]:
        """
        Prepare messages to send to LLM
        
        Note: For Claude API, system prompt should be passed separately via system parameter,
        not as a message. The AgentLLMModel will handle this.
        """
        # Don't add system message here - it will be handled separately by the LLM adapter
        return self.messages