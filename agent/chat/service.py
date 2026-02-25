"""
ChatService - Wraps the Agent stream execution to produce CHAT protocol chunks.

Translates agent events (message_update, message_end, tool_execution_end, etc.)
into the CHAT socket protocol format (content chunks with segment_id, tool_calls chunks).
"""

import time
from typing import Callable, Optional

from common.log import logger


class ChatService:
    """
    High-level service that runs an Agent for a given query and streams
    the results as CHAT protocol chunks via a callback.

    Usage:
        svc = ChatService(agent_bridge)
        svc.run(query, session_id, send_chunk_fn)
    """

    def __init__(self, agent_bridge):
        """
        :param agent_bridge: AgentBridge instance (manages agent lifecycle)
        """
        self.agent_bridge = agent_bridge

    def run(self, query: str, session_id: str, send_chunk_fn: Callable[[dict], None]):
        """
        Run the agent for *query* and stream results back via *send_chunk_fn*.

        The method blocks until the agent finishes. After it returns the SDK
        will automatically send the final (streaming=false) message.

        :param query: user query text
        :param session_id: session identifier for agent isolation
        :param send_chunk_fn: callable(chunk_data: dict) to send a streaming chunk
        """
        agent = self.agent_bridge.get_agent(session_id=session_id)
        if agent is None:
            raise RuntimeError("Failed to initialise agent for the session")

        # State shared between the event callback and this method
        state = _StreamState()

        def on_event(event: dict):
            """Translate agent events into CHAT protocol chunks."""
            event_type = event.get("type")
            data = event.get("data", {})

            if event_type == "message_update":
                # Incremental text delta
                delta = data.get("delta", "")
                if delta:
                    send_chunk_fn({
                        "chunk_type": "content",
                        "delta": delta,
                        "segment_id": state.segment_id,
                    })

            elif event_type == "message_end":
                # A content segment finished.
                tool_calls = data.get("tool_calls", [])
                if tool_calls:
                    # After tool_calls are executed the next content will be
                    # a new segment; collect tool results until turn_end.
                    state.pending_tool_results = []

            elif event_type == "tool_execution_end":
                tool_name = data.get("tool_name", "")
                arguments = data.get("arguments", {})
                result = data.get("result", "")
                status = data.get("status", "unknown")
                execution_time = data.get("execution_time", 0)
                elapsed_str = f"{execution_time:.2f}s"

                # Serialise result to string if needed
                if not isinstance(result, str):
                    import json
                    try:
                        result = json.dumps(result, ensure_ascii=False)
                    except Exception:
                        result = str(result)

                tool_info = {
                    "name": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "status": status,
                    "elapsed": elapsed_str,
                }

                if state.pending_tool_results is not None:
                    state.pending_tool_results.append(tool_info)

            elif event_type == "turn_end":
                has_tool_calls = data.get("has_tool_calls", False)
                if has_tool_calls and state.pending_tool_results:
                    # Flush collected tool results as a single tool_calls chunk
                    send_chunk_fn({
                        "chunk_type": "tool_calls",
                        "tool_calls": state.pending_tool_results,
                    })
                    state.pending_tool_results = None
                    # Next content belongs to a new segment
                    state.segment_id += 1

        # Run the agent with our event callback ---------------------------
        logger.info(f"[ChatService] Starting agent run: session={session_id}, query={query[:80]}")

        from config import conf
        max_context_turns = conf().get("agent_max_context_turns", 30)

        # Get full system prompt with skills
        full_system_prompt = agent.get_full_system_prompt()

        # Create a copy of messages for this execution
        with agent.messages_lock:
            messages_copy = agent.messages.copy()
            original_length = len(agent.messages)

        from agent.protocol.agent_stream import AgentStreamExecutor

        executor = AgentStreamExecutor(
            agent=agent,
            model=agent.model,
            system_prompt=full_system_prompt,
            tools=agent.tools,
            max_turns=agent.max_steps,
            on_event=on_event,
            messages=messages_copy,
            max_context_turns=max_context_turns,
        )

        try:
            response = executor.run_stream(query)
        except Exception:
            # If executor cleared messages (context overflow), sync back
            if len(executor.messages) == 0:
                with agent.messages_lock:
                    agent.messages.clear()
                    logger.info("[ChatService] Cleared agent message history after executor recovery")
            raise

        # Append only the NEW messages from this execution (thread-safe)
        with agent.messages_lock:
            new_messages = executor.messages[original_length:]
            agent.messages.extend(new_messages)

        # Store executor reference for files_to_send access
        agent.stream_executor = executor

        # Execute post-process tools
        agent._execute_post_process_tools()

        logger.info(f"[ChatService] Agent run completed: session={session_id}")



class _StreamState:
    """Mutable state shared between the event callback and the run method."""

    def __init__(self):
        self.segment_id: int = 0
        # None means we are not accumulating tool results right now.
        # A list means we are in the middle of a tool-execution phase.
        self.pending_tool_results: Optional[list] = None
