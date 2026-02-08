"""
Agent Stream Execution Module - Multi-turn reasoning based on tool-call

Provides streaming output, event system, and complete tool-call loop
"""
import json
import time
from typing import List, Dict, Any, Optional, Callable, Tuple

from agent.protocol.models import LLMRequest, LLMModel
from agent.tools.base_tool import BaseTool, ToolResult
from common.log import logger


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
            messages: Optional[List[Dict]] = None,
            max_context_turns: int = 30
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
            max_context_turns: Maximum number of conversation turns to keep in context
        """
        self.agent = agent
        self.model = model
        self.system_prompt = system_prompt
        # Convert tools list to dict
        self.tools = {tool.name: tool for tool in tools} if isinstance(tools, list) else tools
        self.max_turns = max_turns
        self.on_event = on_event
        self.max_context_turns = max_context_turns

        # Message history - use provided messages or create new list
        self.messages = messages if messages is not None else []
        
        # Tool failure tracking for retry protection
        self.tool_failure_history = []  # List of (tool_name, args_hash, success) tuples
        
        # Track files to send (populated by read tool)
        self.files_to_send = []  # List of file metadata dicts

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
    
    def _filter_think_tags(self, text: str) -> str:
        """
        Remove <think> and </think> tags but keep the content inside.
        Some LLM providers (e.g., MiniMax) may return thinking process wrapped in <think> tags.
        We only remove the tags themselves, keeping the actual thinking content.
        """
        if not text:
            return text
        import re
        # Remove only the <think> and </think> tags, keep the content
        text = re.sub(r'<think>', '', text)
        text = re.sub(r'</think>', '', text)
        return text

    def _hash_args(self, args: dict) -> str:
        """Generate a simple hash for tool arguments"""
        import hashlib
        # Sort keys for consistent hashing
        args_str = json.dumps(args, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(args_str.encode()).hexdigest()[:8]
    
    def _check_consecutive_failures(self, tool_name: str, args: dict) -> Tuple[bool, str, bool]:
        """
        Check if tool has failed too many times consecutively or called repeatedly with same args
        
        Returns:
            (should_stop, reason, is_critical)
            - should_stop: Whether to stop tool execution
            - reason: Reason for stopping
            - is_critical: Whether to abort entire conversation (True for 8+ failures)
        """
        args_hash = self._hash_args(args)
        
        # Count consecutive calls (both success and failure) for same tool + args
        # This catches infinite loops where tool succeeds but LLM keeps calling it
        same_args_calls = 0
        for name, ahash, success in reversed(self.tool_failure_history):
            if name == tool_name and ahash == args_hash:
                same_args_calls += 1
            else:
                break  # Different tool or args, stop counting
        
        # Stop at 5 consecutive calls with same args (whether success or failure)
        if same_args_calls >= 5:
            return True, f"工具 '{tool_name}' 使用相同参数已被调用 {same_args_calls} 次，停止执行以防止无限循环。如果需要查看配置，结果已在之前的调用中返回。", False
        
        # Count consecutive failures for same tool + args
        same_args_failures = 0
        for name, ahash, success in reversed(self.tool_failure_history):
            if name == tool_name and ahash == args_hash:
                if not success:
                    same_args_failures += 1
                else:
                    break  # Stop at first success
            else:
                break  # Different tool or args, stop counting
        
        if same_args_failures >= 3:
            return True, f"工具 '{tool_name}' 使用相同参数连续失败 {same_args_failures} 次，停止执行以防止无限循环", False
        
        # Count consecutive failures for same tool (any args)
        same_tool_failures = 0
        for name, ahash, success in reversed(self.tool_failure_history):
            if name == tool_name:
                if not success:
                    same_tool_failures += 1
                else:
                    break  # Stop at first success
            else:
                break  # Different tool, stop counting
        
        # Hard stop at 8 failures - abort with critical message
        if same_tool_failures >= 8:
            return True, f"抱歉，我没能完成这个任务。可能是我理解有误或者当前方法不太合适。\n\n建议你：\n• 换个方式描述需求试试\n• 把任务拆分成更小的步骤\n• 或者换个思路来解决", True
        
        # Warning at 6 failures
        if same_tool_failures >= 6:
            return True, f"工具 '{tool_name}' 连续失败 {same_tool_failures} 次（使用不同参数），停止执行以防止无限循环", False
        
        return False, "", False
    
    def _record_tool_result(self, tool_name: str, args: dict, success: bool):
        """Record tool execution result for failure tracking"""
        args_hash = self._hash_args(args)
        self.tool_failure_history.append((tool_name, args_hash, success))
        # Keep only last 50 records to avoid memory bloat
        if len(self.tool_failure_history) > 50:
            self.tool_failure_history = self.tool_failure_history[-50:]

    def run_stream(self, user_message: str) -> str:
        """
        Execute streaming reasoning loop
        
        Args:
            user_message: User message
            
        Returns:
            Final response text
        """
        # Log user message with model info
        logger.info(f"🤖 {self.model.model} | 👤 {user_message}")
        
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
                logger.info(f"[Agent] 第 {turn} 轮")
                self._emit_event("turn_start", {"turn": turn})

                # Check if memory flush is needed (before calling LLM)
                # 使用独立的 flush 阈值（50K tokens 或 20 轮）
                if self.agent.memory_manager and hasattr(self.agent, 'last_usage'):
                    usage = self.agent.last_usage
                    if usage and 'input_tokens' in usage:
                        current_tokens = usage.get('input_tokens', 0)

                        if self.agent.memory_manager.should_flush_memory(
                                current_tokens=current_tokens
                        ):
                            self._emit_event("memory_flush_start", {
                                "current_tokens": current_tokens,
                                "turn_count": self.agent.memory_manager.flush_manager.turn_count
                            })

                            # TODO: Execute memory flush in background
                            # This would require async support
                            logger.info(
                                f"Memory flush recommended: tokens={current_tokens}, turns={self.agent.memory_manager.flush_manager.turn_count}")

                # Call LLM (enable retry_on_empty for better reliability)
                assistant_msg, tool_calls = self._call_llm_stream(retry_on_empty=True)
                final_response = assistant_msg

                # No tool calls, end loop
                if not tool_calls:
                    # 检查是否返回了空响应
                    if not assistant_msg:
                        logger.warning(f"[Agent] LLM returned empty response after retry (no content and no tool calls)")
                        logger.info(f"[Agent] This usually happens when LLM thinks the task is complete after tool execution")
                        
                        # 如果之前有工具调用，强制要求 LLM 生成文本回复
                        if turn > 1:
                            logger.info(f"[Agent] Requesting explicit response from LLM...")
                            
                            # 添加一条消息，明确要求回复用户
                            self.messages.append({
                                "role": "user",
                                "content": [{
                                    "type": "text",
                                    "text": "请向用户说明刚才工具执行的结果或回答用户的问题。"
                                }]
                            })
                            
                            # 再调用一次 LLM
                            assistant_msg, tool_calls = self._call_llm_stream(retry_on_empty=False)
                            final_response = assistant_msg
                            
                            # 如果还是空，才使用 fallback
                            if not assistant_msg and not tool_calls:
                                logger.warning(f"[Agent] Still empty after explicit request")
                                final_response = (
                                    "抱歉，我暂时无法生成回复。请尝试换一种方式描述你的需求，或稍后再试。"
                                )
                                logger.info(f"Generated fallback response for empty LLM output")
                        else:
                            # 第一轮就空回复，直接 fallback
                            final_response = (
                                "抱歉，我暂时无法生成回复。请尝试换一种方式描述你的需求，或稍后再试。"
                            )
                            logger.info(f"Generated fallback response for empty LLM output")
                    else:
                        logger.info(f"💭 {assistant_msg[:150]}{'...' if len(assistant_msg) > 150 else ''}")
                    
                    logger.debug(f"✅ 完成 (无工具调用)")
                    self._emit_event("turn_end", {
                        "turn": turn,
                        "has_tool_calls": False
                    })
                    break

                # Log tool calls with arguments
                tool_calls_str = []
                for tc in tool_calls:
                    # Safely handle None or missing arguments
                    args = tc.get('arguments') or {}
                    if isinstance(args, dict):
                        args_str = ', '.join([f"{k}={v}" for k, v in args.items()])
                        if args_str:
                            tool_calls_str.append(f"{tc['name']}({args_str})")
                        else:
                            tool_calls_str.append(tc['name'])
                    else:
                        tool_calls_str.append(tc['name'])
                logger.info(f"🔧 {', '.join(tool_calls_str)}")

                # Execute tools
                tool_results = []
                tool_result_blocks = []

                try:
                    for tool_call in tool_calls:
                        result = self._execute_tool(tool_call)
                        tool_results.append(result)
                        
                        # Debug: Check if tool is being called repeatedly with same args
                        if turn > 2:
                            # Check last N tool calls for repeats
                            repeat_count = sum(
                                1 for name, ahash, _ in self.tool_failure_history[-10:]
                                if name == tool_call["name"] and ahash == self._hash_args(tool_call["arguments"])
                            )
                            if repeat_count >= 3:
                                logger.warning(
                                    f"⚠️  Tool '{tool_call['name']}' has been called {repeat_count} times "
                                    f"with same arguments. This may indicate a loop."
                                )
                        
                        # Check if this is a file to send (from read tool)
                        if result.get("status") == "success" and isinstance(result.get("result"), dict):
                            result_data = result.get("result")
                            if result_data.get("type") == "file_to_send":
                                # Store file metadata for later sending
                                self.files_to_send.append(result_data)
                                logger.info(f"📎 检测到待发送文件: {result_data.get('file_name', result_data.get('path'))}")
                        
                        # Check for critical error - abort entire conversation
                        if result.get("status") == "critical_error":
                            logger.error(f"💥 检测到严重错误，终止对话")
                            final_response = result.get('result', '任务执行失败')
                            return final_response
                        
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

                        # Truncate excessively large tool results for the current turn
                        # Historical turns will be further truncated in _trim_messages()
                        MAX_CURRENT_TURN_RESULT_CHARS = 50000
                        if len(result_content) > MAX_CURRENT_TURN_RESULT_CHARS:
                            truncated_len = len(result_content)
                            result_content = result_content[:MAX_CURRENT_TURN_RESULT_CHARS] + \
                                f"\n\n[Output truncated: {truncated_len} chars total, showing first {MAX_CURRENT_TURN_RESULT_CHARS} chars]"
                            logger.info(f"📎 Truncated tool result for '{tool_call['name']}': {truncated_len} -> {MAX_CURRENT_TURN_RESULT_CHARS} chars")

                        tool_result_block = {
                            "type": "tool_result",
                            "tool_use_id": tool_call["id"],
                            "content": result_content
                        }
                        
                        # Add is_error field for Claude API (helps model understand failures)
                        if is_error:
                            tool_result_block["is_error"] = True
                        
                        tool_result_blocks.append(tool_result_block)
                
                finally:
                    # CRITICAL: Always add tool_result to maintain message history integrity
                    # Even if tool execution fails, we must add error results to match tool_use
                    if tool_result_blocks:
                        # Add tool results to message history as user message (Claude format)
                        self.messages.append({
                            "role": "user",
                            "content": tool_result_blocks
                        })
                        
                        # Detect potential infinite loop: same tool called multiple times with success
                        # If detected, add a hint to LLM to stop calling tools and provide response
                        if turn >= 3 and len(tool_calls) > 0:
                            tool_name = tool_calls[0]["name"]
                            args_hash = self._hash_args(tool_calls[0]["arguments"])
                            
                            # Count recent successful calls with same tool+args
                            recent_success_count = 0
                            for name, ahash, success in reversed(self.tool_failure_history[-10:]):
                                if name == tool_name and ahash == args_hash and success:
                                    recent_success_count += 1
                            
                            # If tool was called successfully 3+ times with same args, add hint to stop loop
                            if recent_success_count >= 3:
                                logger.warning(
                                    f"⚠️  Detected potential loop: '{tool_name}' called {recent_success_count} times "
                                    f"with same args. Adding hint to LLM to provide final response."
                                )
                                # Add a gentle hint message to guide LLM to respond
                                self.messages.append({
                                    "role": "user",
                                    "content": [{
                                        "type": "text",
                                        "text": "工具已成功执行并返回结果。请基于这些信息向用户做出回复，不要重复调用相同的工具。"
                                    }]
                                })
                    elif tool_calls:
                        # If we have tool_calls but no tool_result_blocks (unexpected error),
                        # create error results for all tool calls to maintain message integrity
                        logger.warning("⚠️ Tool execution interrupted, adding error results to maintain message history")
                        emergency_blocks = []
                        for tool_call in tool_calls:
                            emergency_blocks.append({
                                "type": "tool_result",
                                "tool_use_id": tool_call["id"],
                                "content": "Error: Tool execution was interrupted",
                                "is_error": True
                            })
                        self.messages.append({
                            "role": "user",
                            "content": emergency_blocks
                        })

                self._emit_event("turn_end", {
                    "turn": turn,
                    "has_tool_calls": True,
                    "tool_count": len(tool_calls)
                })

            if turn >= self.max_turns:
                logger.warning(f"⚠️  已达到最大决策步数限制: {self.max_turns}")
                
                # Force model to summarize without tool calls
                logger.info(f"[Agent] Requesting summary from LLM after reaching max steps...")
                
                # Add a system message to force summary
                self.messages.append({
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": f"你已经执行了{turn}个决策步骤，达到了单次运行的最大步数限制。请总结一下你目前的执行过程和结果，告诉用户当前的进展情况。不要再调用工具，直接用文字回复。"
                    }]
                })
                
                # Call LLM one more time to get summary (without retry to avoid loops)
                try:
                    summary_response, summary_tools = self._call_llm_stream(retry_on_empty=False)
                    if summary_response:
                        final_response = summary_response
                        logger.info(f"💭 Summary: {summary_response[:150]}{'...' if len(summary_response) > 150 else ''}")
                    else:
                        # Fallback if model still doesn't respond
                        final_response = (
                            f"我已经执行了{turn}个决策步骤，达到了单次运行的步数上限。"
                            "任务可能还未完全完成，建议你将任务拆分成更小的步骤，或者换一种方式描述需求。"
                        )
                except Exception as e:
                    logger.warning(f"Failed to get summary from LLM: {e}")
                    final_response = (
                        f"我已经执行了{turn}个决策步骤，达到了单次运行的步数上限。"
                        "任务可能还未完全完成，建议你将任务拆分成更小的步骤，或者换一种方式描述需求。"
                    )

        except Exception as e:
            logger.error(f"❌ Agent执行错误: {e}")
            self._emit_event("error", {"error": str(e)})
            raise

        finally:
            logger.info(f"[Agent] 🏁 完成 ({turn}轮)")
            self._emit_event("agent_end", {"final_response": final_response})

            # 每轮对话结束后增加计数（用户消息+AI回复=1轮）
            if self.agent.memory_manager:
                self.agent.memory_manager.increment_turn()

        return final_response

    def _call_llm_stream(self, retry_on_empty=True, retry_count=0, max_retries=3,
                         _overflow_retry: bool = False) -> Tuple[str, List[Dict]]:
        """
        Call LLM with streaming and automatic retry on errors
        
        Args:
            retry_on_empty: Whether to retry once if empty response is received
            retry_count: Current retry attempt (internal use)
            max_retries: Maximum number of retries for API errors
            _overflow_retry: Internal flag indicating this is a retry after context overflow
        
        Returns:
            (response_text, tool_calls)
        """
        # Validate and fix message history first
        self._validate_and_fix_messages()
        
        # Trim messages if needed (using agent's context management)
        self._trim_messages()

        # Prepare messages
        messages = self._prepare_messages()
        logger.debug(f"Sending {len(messages)} messages to LLM")

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
        stop_reason = None  # Track why the stream stopped

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
                        error_type = error_data.get("type", "")
                    else:
                        error_msg = chunk.get("message", str(error_data))
                        error_code = ""
                        error_type = ""
                    
                    status_code = chunk.get("status_code", "N/A")
                    
                    # Log error with all available information
                    logger.error(f"🔴 Stream API Error:")
                    logger.error(f"   Message: {error_msg}")
                    logger.error(f"   Status Code: {status_code}")
                    logger.error(f"   Error Code: {error_code}")
                    logger.error(f"   Error Type: {error_type}")
                    logger.error(f"   Full chunk: {chunk}")
                    
                    # Check if this is a context overflow error (keyword-based, works for all models)
                    # Don't rely on specific status codes as different providers use different codes
                    error_msg_lower = error_msg.lower()
                    is_overflow = any(keyword in error_msg_lower for keyword in [
                        'context length exceeded', 'maximum context length', 'prompt is too long',
                        'context overflow', 'context window', 'too large', 'exceeds model context',
                        'request_too_large', 'request exceeds the maximum size', 'tokens exceed'
                    ])
                    
                    if is_overflow:
                        # Mark as context overflow for special handling
                        raise Exception(f"[CONTEXT_OVERFLOW] {error_msg} (Status: {status_code})")
                    else:
                        # Raise exception with full error message for retry logic
                        raise Exception(f"{error_msg} (Status: {status_code}, Code: {error_code}, Type: {error_type})")

                # Parse chunk
                if isinstance(chunk, dict) and "choices" in chunk:
                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})
                    
                    # Capture finish_reason if present
                    finish_reason = choice.get("finish_reason")
                    if finish_reason:
                        stop_reason = finish_reason

                    # Handle text content
                    content_delta = delta.get("content") or ""
                    if content_delta:
                        # Filter out <think> tags from content
                        filtered_delta = self._filter_think_tags(content_delta)
                        full_content += filtered_delta
                        if filtered_delta:  # Only emit if there's content after filtering
                            self._emit_event("message_update", {"delta": filtered_delta})

                    # Handle tool calls
                    if "tool_calls" in delta and delta["tool_calls"]:
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
            error_str = str(e)
            error_str_lower = error_str.lower()
            
            # Check if error is context overflow (non-retryable, needs session reset)
            # Method 1: Check for special marker (set in stream error handling above)
            is_context_overflow = '[context_overflow]' in error_str_lower
            
            # Method 2: Fallback to keyword matching for non-stream errors
            if not is_context_overflow:
                is_context_overflow = any(keyword in error_str_lower for keyword in [
                    'context length exceeded', 'maximum context length', 'prompt is too long',
                    'context overflow', 'context window', 'too large', 'exceeds model context',
                    'request_too_large', 'request exceeds the maximum size'
                ])
            
            # Check if error is message format error (incomplete tool_use/tool_result pairs)
            # This happens when previous conversation had tool failures
            is_message_format_error = any(keyword in error_str_lower for keyword in [
                'tool_use', 'tool_result', 'without', 'immediately after',
                'corresponding', 'must have', 'each'
            ]) and 'status: 400' in error_str_lower
            
            if is_context_overflow or is_message_format_error:
                error_type = "context overflow" if is_context_overflow else "message format error"
                logger.error(f"💥 {error_type} detected: {e}")

                # Strategy: try aggressive trimming first, only clear as last resort
                if is_context_overflow and not _overflow_retry:
                    trimmed = self._aggressive_trim_for_overflow()
                    if trimmed:
                        logger.warning("🔄 Aggressively trimmed context, retrying...")
                        return self._call_llm_stream(
                            retry_on_empty=retry_on_empty,
                            retry_count=retry_count,
                            max_retries=max_retries,
                            _overflow_retry=True
                        )

                # Aggressive trim didn't help or this is a message format error
                # -> clear everything
                logger.warning("🔄 Clearing conversation history to recover")
                self.messages.clear()
                if is_context_overflow:
                    raise Exception(
                        "抱歉，对话历史过长导致上下文溢出。我已清空历史记录，请重新描述你的需求。"
                    )
                else:
                    raise Exception(
                        "抱歉，之前的对话出现了问题。我已清空历史记录，请重新发送你的消息。"
                    )
            
            # Check if error is rate limit (429)
            is_rate_limit = '429' in error_str_lower or 'rate limit' in error_str_lower
            
            # Check if error is retryable (timeout, connection, server busy, etc.)
            is_retryable = any(keyword in error_str_lower for keyword in [
                'timeout', 'timed out', 'connection', 'network', 
                'rate limit', 'overloaded', 'unavailable', 'busy', 'retry',
                '429', '500', '502', '503', '504', '512'
            ])
            
            if is_retryable and retry_count < max_retries:
                # Rate limit needs longer wait time
                if is_rate_limit:
                    wait_time = 30 + (retry_count * 15)  # 30s, 45s, 60s for rate limit
                else:
                    wait_time = (retry_count + 1) * 2  # 2s, 4s, 6s for other errors
                
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

            # Ensure tool call has a valid ID (some providers return empty/None IDs)
            tool_id = tc.get("id") or ""
            if not tool_id:
                import uuid
                tool_id = f"call_{uuid.uuid4().hex[:24]}"

            try:
                # Safely get arguments, handle None case
                args_str = tc.get("arguments") or ""
                arguments = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError as e:
                # Handle None or invalid arguments safely
                args_str = tc.get('arguments') or ""
                args_preview = args_str[:200] if len(args_str) > 200 else args_str
                logger.error(f"Failed to parse tool arguments for {tc['name']}")
                logger.error(f"Arguments length: {len(args_str)} chars")
                logger.error(f"Arguments preview: {args_preview}...")
                logger.error(f"JSON decode error: {e}")

                # Return a clear error message to the LLM instead of empty dict
                # This helps the LLM understand what went wrong
                tool_calls.append({
                    "id": tool_id,
                    "name": tc["name"],
                    "arguments": {},
                    "_parse_error": f"Invalid JSON in tool arguments: {args_preview}... Error: {str(e)}. Tip: For large content, consider splitting into smaller chunks or using a different approach."
                })
                continue

            tool_calls.append({
                "id": tool_id,
                "name": tc["name"],
                "arguments": arguments
            })

        # Check for empty response and retry once if enabled
        if retry_on_empty and not full_content and not tool_calls:
            logger.warning(f"⚠️  LLM returned empty response (stop_reason: {stop_reason}), retrying once...")
            self._emit_event("message_end", {
                "content": "",
                "tool_calls": [],
                "empty_retry": True,
                "stop_reason": stop_reason
            })
            # Retry without retry flag to avoid infinite loop
            return self._call_llm_stream(
                retry_on_empty=False, 
                retry_count=retry_count,
                max_retries=max_retries
            )

        # Filter full_content one more time (in case tags were split across chunks)
        full_content = self._filter_think_tags(full_content)
        
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
                    "id": tc.get("id", ""),
                    "name": tc.get("name", ""),
                    "input": tc.get("arguments", {})
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

        # Check if there was a JSON parse error
        if "_parse_error" in tool_call:
            parse_error = tool_call["_parse_error"]
            logger.error(f"Skipping tool execution due to parse error: {parse_error}")
            result = {
                "status": "error",
                "result": f"Failed to parse tool arguments. {parse_error}. Please ensure your tool call uses valid JSON format with all required parameters.",
                "execution_time": 0
            }
            self._record_tool_result(tool_name, arguments, False)
            return result

        # Check for consecutive failures (retry protection)
        should_stop, stop_reason, is_critical = self._check_consecutive_failures(tool_name, arguments)
        if should_stop:
            logger.error(f"🛑 {stop_reason}")
            self._record_tool_result(tool_name, arguments, False)
            
            if is_critical:
                # Critical failure - abort entire conversation
                result = {
                    "status": "critical_error",
                    "result": stop_reason,
                    "execution_time": 0
                }
            else:
                # Normal failure - let LLM try different approach
                result = {
                    "status": "error",
                    "result": f"{stop_reason}\n\n当前方法行不通，请尝试完全不同的方法或向用户询问更多信息。",
                    "execution_time": 0
                }
            return result

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

            # Record tool result for failure tracking
            success = result.status == "success"
            self._record_tool_result(tool_name, arguments, success)

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
            # Record failure
            self._record_tool_result(tool_name, arguments, False)
            
            self._emit_event("tool_execution_end", {
                "tool_call_id": tool_id,
                "tool_name": tool_name,
                **error_result
            })
            return error_result

    def _validate_and_fix_messages(self):
        """
        Validate message history and fix incomplete tool_use/tool_result pairs.
        Claude API requires each tool_use to have a corresponding tool_result immediately after.
        """
        if not self.messages:
            return
        
        # Check last message for incomplete tool_use
        if len(self.messages) > 0:
            last_msg = self.messages[-1]
            if last_msg.get("role") == "assistant":
                # Check if assistant message has tool_use blocks
                content = last_msg.get("content", [])
                if isinstance(content, list):
                    has_tool_use = any(block.get("type") == "tool_use" for block in content)
                    if has_tool_use:
                        # This is incomplete - remove it
                        logger.warning(f"⚠️ Removing incomplete tool_use message from history")
                        self.messages.pop()

    def _identify_complete_turns(self) -> List[Dict]:
        """
        识别完整的对话轮次
        
        一个完整轮次包括：
        1. 用户消息（text）
        2. AI 回复（可能包含 tool_use）
        3. 工具结果（tool_result，如果有）
        4. 后续 AI 回复（如果有）
        
        Returns:
            List of turns, each turn is a dict with 'messages' list
        """
        turns = []
        current_turn = {'messages': []}
        
        for msg in self.messages:
            role = msg.get('role')
            content = msg.get('content', [])
            
            if role == 'user':
                # 检查是否是用户查询（不是工具结果）
                is_user_query = False
                if isinstance(content, list):
                    is_user_query = any(
                        block.get('type') == 'text' 
                        for block in content 
                        if isinstance(block, dict)
                    )
                elif isinstance(content, str):
                    is_user_query = True
                
                if is_user_query:
                    # 开始新轮次
                    if current_turn['messages']:
                        turns.append(current_turn)
                    current_turn = {'messages': [msg]}
                else:
                    # 工具结果，属于当前轮次
                    current_turn['messages'].append(msg)
            else:
                # AI 回复，属于当前轮次
                current_turn['messages'].append(msg)
        
        # 添加最后一个轮次
        if current_turn['messages']:
            turns.append(current_turn)
        
        return turns
    
    def _estimate_turn_tokens(self, turn: Dict) -> int:
        """估算一个轮次的 tokens"""
        return sum(
            self.agent._estimate_message_tokens(msg) 
            for msg in turn['messages']
        )

    def _truncate_historical_tool_results(self):
        """
        Truncate tool_result content in historical messages to reduce context size.

        Current turn results are kept at 30K chars (truncated at creation time).
        Historical turn results are further truncated to 10K chars here.
        This runs before token-based trimming so that we first shrink oversized
        results, potentially avoiding the need to drop entire turns.
        """
        MAX_HISTORY_RESULT_CHARS = 20000

        if len(self.messages) < 2:
            return

        # Find where the last user text message starts (= current turn boundary)
        # We skip the current turn's messages to preserve their full content
        current_turn_start = len(self.messages)
        for i in range(len(self.messages) - 1, -1, -1):
            msg = self.messages[i]
            if msg.get("role") == "user":
                content = msg.get("content", [])
                if isinstance(content, list) and any(
                    isinstance(b, dict) and b.get("type") == "text" for b in content
                ):
                    current_turn_start = i
                    break
                elif isinstance(content, str):
                    current_turn_start = i
                    break

        truncated_count = 0
        for i in range(current_turn_start):
            msg = self.messages[i]
            if msg.get("role") != "user":
                continue
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                result_str = block.get("content", "")
                if isinstance(result_str, str) and len(result_str) > MAX_HISTORY_RESULT_CHARS:
                    original_len = len(result_str)
                    block["content"] = result_str[:MAX_HISTORY_RESULT_CHARS] + \
                        f"\n\n[Historical output truncated: {original_len} -> {MAX_HISTORY_RESULT_CHARS} chars]"
                    truncated_count += 1

        if truncated_count > 0:
            logger.info(f"📎 Truncated {truncated_count} historical tool result(s) to {MAX_HISTORY_RESULT_CHARS} chars")

    def _aggressive_trim_for_overflow(self) -> bool:
        """
        Aggressively trim context when a real overflow error is returned by the API.

        This method goes beyond normal _trim_messages by:
        1. Truncating all tool results (including current turn) to a small limit
        2. Keeping only the last 5 complete conversation turns
        3. Truncating overly long user messages

        Returns:
            True if messages were trimmed (worth retrying), False if nothing left to trim
        """
        if not self.messages:
            return False

        original_count = len(self.messages)

        # Step 1: Aggressively truncate ALL tool results to 5K chars
        AGGRESSIVE_LIMIT = 10000
        truncated = 0
        for msg in self.messages:
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                # Truncate tool_result blocks
                if block.get("type") == "tool_result":
                    result_str = block.get("content", "")
                    if isinstance(result_str, str) and len(result_str) > AGGRESSIVE_LIMIT:
                        block["content"] = (
                            result_str[:AGGRESSIVE_LIMIT]
                            + f"\n\n[Truncated for context recovery: "
                            f"{len(result_str)} -> {AGGRESSIVE_LIMIT} chars]"
                        )
                        truncated += 1
                # Truncate tool_use input blocks (e.g. large write content)
                if block.get("type") == "tool_use" and isinstance(block.get("input"), dict):
                    input_str = json.dumps(block["input"], ensure_ascii=False)
                    if len(input_str) > AGGRESSIVE_LIMIT:
                        # Keep only a summary of the input
                        for key, val in block["input"].items():
                            if isinstance(val, str) and len(val) > 1000:
                                block["input"][key] = (
                                    val[:1000]
                                    + f"... [truncated {len(val)} chars]"
                                )
                        truncated += 1

        # Step 2: Truncate overly long user text messages (e.g. pasted content)
        USER_MSG_LIMIT = 10000
        for msg in self.messages:
            if msg.get("role") != "user":
                continue
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if len(text) > USER_MSG_LIMIT:
                            block["text"] = (
                                text[:USER_MSG_LIMIT]
                                + f"\n\n[Message truncated for context recovery: "
                                f"{len(text)} -> {USER_MSG_LIMIT} chars]"
                            )
                            truncated += 1
            elif isinstance(content, str) and len(content) > USER_MSG_LIMIT:
                msg["content"] = (
                    content[:USER_MSG_LIMIT]
                    + f"\n\n[Message truncated for context recovery: "
                    f"{len(content)} -> {USER_MSG_LIMIT} chars]"
                )
                truncated += 1

        # Step 3: Keep only the last 5 complete turns
        turns = self._identify_complete_turns()
        if len(turns) > 5:
            kept_turns = turns[-5:]
            new_messages = []
            for turn in kept_turns:
                new_messages.extend(turn["messages"])
            removed = len(turns) - 5
            self.messages[:] = new_messages
            logger.info(
                f"🔧 Aggressive trim: removed {removed} old turns, "
                f"truncated {truncated} large blocks, "
                f"{original_count} -> {len(self.messages)} messages"
            )
            return True

        if truncated > 0:
            logger.info(
                f"🔧 Aggressive trim: truncated {truncated} large blocks "
                f"(no turns removed, only {len(turns)} turn(s) left)"
            )
            return True

        # Nothing left to trim
        logger.warning("🔧 Aggressive trim: nothing to trim, will clear history")
        return False

    def _trim_messages(self):
        """
        智能清理消息历史，保持对话完整性

        使用完整轮次作为清理单位，确保：
        1. 不会在对话中间截断
        2. 工具调用链（tool_use + tool_result）保持完整
        3. 每轮对话都是完整的（用户消息 + AI回复 + 工具调用）
        """
        if not self.messages or not self.agent:
            return

        # Step 0: Truncate large tool results in historical turns (30K -> 10K)
        self._truncate_historical_tool_results()

        # Step 1: 识别完整轮次
        turns = self._identify_complete_turns()
        
        if not turns:
            return
        
        # Step 2: 轮次限制 - 保留最近 N 轮
        if len(turns) > self.max_context_turns:
            removed_turns = len(turns) - self.max_context_turns
            turns = turns[-self.max_context_turns:]  # 保留最近的轮次
            
            logger.info(
                f"💾 上下文轮次超限: {len(turns) + removed_turns} > {self.max_context_turns}，"
                f"移除最早的 {removed_turns} 轮完整对话"
            )

        # Step 3: Token 限制 - 保留完整轮次
        # Get context window from agent (based on model)
        context_window = self.agent._get_model_context_window()

        # Use configured max_context_tokens if available
        if hasattr(self.agent, 'max_context_tokens') and self.agent.max_context_tokens:
            max_tokens = self.agent.max_context_tokens
        else:
            # Reserve 10% for response generation
            reserve_tokens = int(context_window * 0.1)
            max_tokens = context_window - reserve_tokens

        # Estimate system prompt tokens
        system_tokens = self.agent._estimate_message_tokens({"role": "system", "content": self.system_prompt})
        available_tokens = max_tokens - system_tokens

        # Calculate current tokens
        current_tokens = sum(self._estimate_turn_tokens(turn) for turn in turns)
        
        # If under limit, reconstruct messages and return
        if current_tokens + system_tokens <= max_tokens:
            # Reconstruct message list from turns
            new_messages = []
            for turn in turns:
                new_messages.extend(turn['messages'])
            
            old_count = len(self.messages)
            self.messages = new_messages
            
            # Log if we removed messages due to turn limit
            if old_count > len(self.messages):
                logger.info(f"   重建消息列表: {old_count} -> {len(self.messages)} 条消息")
            return

        # Token limit exceeded - keep complete turns from newest
        logger.info(
            f"🔄 上下文tokens超限: ~{current_tokens + system_tokens} > {max_tokens}，"
            f"将按完整轮次移除最早的对话"
        )

        # 从最新轮次开始，反向累加（保持完整轮次）
        kept_turns = []
        accumulated_tokens = 0
        min_turns = 3  # 尽量保留至少 3 轮，但不强制（避免超出 token 限制）
        
        for i, turn in enumerate(reversed(turns)):
            turn_tokens = self._estimate_turn_tokens(turn)
            turns_from_end = i + 1
            
            # 检查是否超出限制
            if accumulated_tokens + turn_tokens <= available_tokens:
                kept_turns.insert(0, turn)
                accumulated_tokens += turn_tokens
            else:
                # 超出限制
                # 如果还没有保留足够的轮次，且这是最后的机会，尝试保留
                if len(kept_turns) < min_turns and turns_from_end <= min_turns:
                    # 检查是否严重超出（超出 20% 以上则放弃）
                    overflow_ratio = (accumulated_tokens + turn_tokens - available_tokens) / available_tokens
                    if overflow_ratio < 0.2:  # 允许最多超出 20%
                        kept_turns.insert(0, turn)
                        accumulated_tokens += turn_tokens
                        logger.debug(f"   为保留最少轮次，允许超出 {overflow_ratio*100:.1f}%")
                        continue
                # 停止保留更早的轮次
                break
        
        # 重建消息列表
        new_messages = []
        for turn in kept_turns:
            new_messages.extend(turn['messages'])
        
        old_count = len(self.messages)
        old_turn_count = len(turns)
        self.messages = new_messages
        new_count = len(self.messages)
        new_turn_count = len(kept_turns)
        
        if old_count > new_count:
            logger.info(
                f"   移除了 {old_turn_count - new_turn_count} 轮对话 "
                f"({old_count} -> {new_count} 条消息，"
                f"~{current_tokens + system_tokens} -> ~{accumulated_tokens + system_tokens} tokens)"
            )

    def _prepare_messages(self) -> List[Dict[str, Any]]:
        """
        Prepare messages to send to LLM
        
        Note: For Claude API, system prompt should be passed separately via system parameter,
        not as a message. The AgentLLMModel will handle this.
        """
        # Don't add system message here - it will be handled separately by the LLM adapter
        return self.messages