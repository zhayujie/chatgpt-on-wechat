import json
import time

from common.log import logger
from agent.protocol.models import LLMRequest, LLMModel
from agent.protocol.agent_stream import AgentStreamExecutor
from agent.protocol.result import AgentAction, AgentActionType, ToolResult, AgentResult
from agent.tools.base_tool import BaseTool, ToolStage


class Agent:
    def __init__(self, system_prompt: str, description: str = "AI Agent", model: LLMModel = None,
                 tools=None, output_mode="print", max_steps=100, max_context_tokens=None, 
                 context_reserve_tokens=None, memory_manager=None, name: str = None):
        """
        Initialize the Agent with system prompt, model, description.

        :param system_prompt: The system prompt for the agent.
        :param description: A description of the agent.
        :param model: An instance of LLMModel to be used by the agent.
        :param tools: Optional list of tools for the agent to use.
        :param output_mode: Control how execution progress is displayed: 
                           "print" for console output or "logger" for using logger
        :param max_steps: Maximum number of steps the agent can take (default: 100)
        :param max_context_tokens: Maximum tokens to keep in context (default: None, auto-calculated based on model)
        :param context_reserve_tokens: Reserve tokens for new requests (default: None, auto-calculated)
        :param memory_manager: Optional MemoryManager instance for memory operations
        :param name: [Deprecated] The name of the agent (no longer used in single-agent system)
        """
        self.name = name or "Agent"
        self.system_prompt = system_prompt
        self.model: LLMModel = model  # Instance of LLMModel
        self.description = description
        self.tools: list = []
        self.max_steps = max_steps  # max tool-call steps, default 100
        self.max_context_tokens = max_context_tokens  # max tokens in context
        self.context_reserve_tokens = context_reserve_tokens  # reserve tokens for new requests
        self.captured_actions = []  # Initialize captured actions list
        self.output_mode = output_mode
        self.last_usage = None  # Store last API response usage info
        self.messages = []  # Unified message history for stream mode
        self.memory_manager = memory_manager  # Memory manager for auto memory flush
        if tools:
            for tool in tools:
                self.add_tool(tool)

    def add_tool(self, tool: BaseTool):
        """
        Add a tool to the agent.

        :param tool: The tool to add (either a tool instance or a tool name)
        """
        # If tool is already an instance, use it directly
        tool.model = self.model
        self.tools.append(tool)

    def _get_model_context_window(self) -> int:
        """
        Get the model's context window size in tokens.
        Auto-detect based on model name.
        
        Model context windows:
        - Claude 3.5/3.7 Sonnet: 200K tokens
        - Claude 3 Opus: 200K tokens
        - GPT-4 Turbo/128K: 128K tokens
        - GPT-4: 8K-32K tokens
        - GPT-3.5: 16K tokens
        - DeepSeek: 64K tokens
        
        :return: Context window size in tokens
        """
        if self.model and hasattr(self.model, 'model'):
            model_name = self.model.model.lower()

            # Claude models - 200K context
            if 'claude-3' in model_name or 'claude-sonnet' in model_name:
                return 200000

            # GPT-4 models
            elif 'gpt-4' in model_name:
                if 'turbo' in model_name or '128k' in model_name:
                    return 128000
                elif '32k' in model_name:
                    return 32000
                else:
                    return 8000

            # GPT-3.5
            elif 'gpt-3.5' in model_name:
                if '16k' in model_name:
                    return 16000
                else:
                    return 4000

            # DeepSeek
            elif 'deepseek' in model_name:
                return 64000

        # Default conservative value
        return 10000

    def _get_context_reserve_tokens(self) -> int:
        """
        Get the number of tokens to reserve for new requests.
        This prevents context overflow by keeping a buffer.
        
        :return: Number of tokens to reserve
        """
        if self.context_reserve_tokens is not None:
            return self.context_reserve_tokens

        # Reserve ~20% of context window for new requests
        context_window = self._get_model_context_window()
        return max(4000, int(context_window * 0.2))

    def _estimate_message_tokens(self, message: dict) -> int:
        """
        Estimate token count for a message using chars/4 heuristic.
        This is a conservative estimate (tends to overestimate).

        :param message: Message dict with 'role' and 'content'
        :return: Estimated token count
        """
        content = message.get('content', '')
        if isinstance(content, str):
            return max(1, len(content) // 4)
        elif isinstance(content, list):
            # Handle multi-part content (text + images)
            total_chars = 0
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'text':
                    total_chars += len(part.get('text', ''))
                elif isinstance(part, dict) and part.get('type') == 'image':
                    # Estimate images as ~1200 tokens
                    total_chars += 4800
            return max(1, total_chars // 4)
        return 1

    def _find_tool(self, tool_name: str):
        """Find and return a tool with the specified name"""
        for tool in self.tools:
            if tool.name == tool_name:
                # Only pre-process stage tools can be actively called
                if tool.stage == ToolStage.PRE_PROCESS:
                    tool.model = self.model
                    tool.context = self  # Set tool context
                    return tool
                else:
                    # If it's a post-process tool, return None to prevent direct calling
                    logger.warning(f"Tool {tool_name} is a post-process tool and cannot be called directly.")
                    return None
        return None

    # output function based on mode
    def output(self, message="", end="\n"):
        if self.output_mode == "print":
            print(message, end=end)
        elif message:
            logger.info(message)

    def _execute_post_process_tools(self):
        """Execute all post-process stage tools"""
        # Get all post-process stage tools
        post_process_tools = [tool for tool in self.tools if tool.stage == ToolStage.POST_PROCESS]

        # Execute each tool
        for tool in post_process_tools:
            # Set tool context
            tool.context = self

            # Record start time for execution timing
            start_time = time.time()

            # Execute tool (with empty parameters, tool will extract needed info from context)
            result = tool.execute({})

            # Calculate execution time
            execution_time = time.time() - start_time

            # Capture tool use for tracking
            self.capture_tool_use(
                tool_name=tool.name,
                input_params={},  # Post-process tools typically don't take parameters
                output=result.result,
                status=result.status,
                error_message=str(result.result) if result.status == "error" else None,
                execution_time=execution_time
            )

            # Log result
            if result.status == "success":
                # Print tool execution result in the desired format
                self.output(f"\n🛠️ {tool.name}: {json.dumps(result.result)}")
            else:
                # Print failure in print mode
                self.output(f"\n🛠️ {tool.name}: {json.dumps({'status': 'error', 'message': str(result.result)})}")

    def capture_tool_use(self, tool_name, input_params, output, status, thought=None, error_message=None,
                         execution_time=0.0):
        """
        Capture a tool use action.
        
        :param thought: thought content
        :param tool_name: Name of the tool used
        :param input_params: Parameters passed to the tool
        :param output: Output from the tool
        :param status: Status of the tool execution
        :param error_message: Error message if the tool execution failed
        :param execution_time: Time taken to execute the tool
        """
        tool_result = ToolResult(
            tool_name=tool_name,
            input_params=input_params,
            output=output,
            status=status,
            error_message=error_message,
            execution_time=execution_time
        )

        action = AgentAction(
            agent_id=self.id if hasattr(self, 'id') else str(id(self)),
            agent_name=self.name,
            action_type=AgentActionType.TOOL_USE,
            tool_result=tool_result,
            thought=thought
        )

        self.captured_actions.append(action)

        return action

    def run_stream(self, user_message: str, on_event=None, clear_history: bool = False) -> str:
        """
        Execute single agent task with streaming (based on tool-call)

        This method supports:
        - Streaming output
        - Multi-turn reasoning based on tool-call
        - Event callbacks
        - Persistent conversation history across calls

        Args:
            user_message: User message
            on_event: Event callback function callback(event: dict)
                     event = {"type": str, "timestamp": float, "data": dict}
            clear_history: If True, clear conversation history before this call (default: False)

        Returns:
            Final response text

        Example:
            # Multi-turn conversation with memory
            response1 = agent.run_stream("My name is Alice")
            response2 = agent.run_stream("What's my name?")  # Will remember Alice

            # Single-turn without memory
            response = agent.run_stream("Hello", clear_history=True)
        """
        # Clear history if requested
        if clear_history:
            self.messages = []

        # Get model to use
        if not self.model:
            raise ValueError("No model available for agent")

        # Create stream executor with agent's message history
        executor = AgentStreamExecutor(
            agent=self,
            model=self.model,
            system_prompt=self.system_prompt,
            tools=self.tools,
            max_turns=self.max_steps,
            on_event=on_event,
            messages=self.messages  # Pass agent's message history
        )

        # Execute
        response = executor.run_stream(user_message)

        # Update agent's message history from executor
        self.messages = executor.messages

        # Execute all post-process tools
        self._execute_post_process_tools()

        return response

    def clear_history(self):
        """Clear conversation history and captured actions"""
        self.messages = []
        self.captured_actions = []