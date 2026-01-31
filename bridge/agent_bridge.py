"""
Agent Bridge - Integrates Agent system with existing COW bridge
"""

from typing import Optional, List

from agent.protocol import Agent, LLMModel, LLMRequest
from bot.openai_compatible_bot import OpenAICompatibleBot
from bridge.bridge import Bridge
from bridge.context import Context
from bridge.reply import Reply, ReplyType
from common import const
from common.log import logger


def add_openai_compatible_support(bot_instance):
    """
    Dynamically add OpenAI-compatible tool calling support to a bot instance.
    
    This allows any bot to gain tool calling capability without modifying its code,
    as long as it uses OpenAI-compatible API format.
    """
    if hasattr(bot_instance, 'call_with_tools'):
        # Bot already has tool calling support
        return bot_instance

    # Create a temporary mixin class that combines the bot with OpenAI compatibility
    class EnhancedBot(bot_instance.__class__, OpenAICompatibleBot):
        """Dynamically enhanced bot with OpenAI-compatible tool calling"""

        def get_api_config(self):
            """
            Infer API config from common configuration patterns.
            Most OpenAI-compatible bots use similar configuration.
            """
            from config import conf

            return {
                'api_key': conf().get("open_ai_api_key"),
                'api_base': conf().get("open_ai_api_base"),
                'model': conf().get("model", "gpt-3.5-turbo"),
                'default_temperature': conf().get("temperature", 0.9),
                'default_top_p': conf().get("top_p", 1.0),
                'default_frequency_penalty': conf().get("frequency_penalty", 0.0),
                'default_presence_penalty': conf().get("presence_penalty", 0.0),
            }

    # Change the bot's class to the enhanced version
    bot_instance.__class__ = EnhancedBot
    logger.info(
        f"[AgentBridge] Enhanced {bot_instance.__class__.__bases__[0].__name__} with OpenAI-compatible tool calling")

    return bot_instance


class AgentLLMModel(LLMModel):
    """
    LLM Model adapter that uses COW's existing bot infrastructure
    """

    def __init__(self, bridge: Bridge, bot_type: str = "chat"):
        # Get model name directly from config
        from config import conf
        model_name = conf().get("model", const.GPT_41)
        super().__init__(model=model_name)
        self.bridge = bridge
        self.bot_type = bot_type
        self._bot = None
        self._use_linkai = conf().get("use_linkai", False) and conf().get("linkai_api_key")
    
    @property
    def bot(self):
        """Lazy load the bot and enhance it with tool calling if needed"""
        if self._bot is None:
            # If use_linkai is enabled, use LinkAI bot directly
            if self._use_linkai:
                self._bot = self.bridge.find_chat_bot(const.LINKAI)
            else:
                self._bot = self.bridge.get_bot(self.bot_type)
                # Automatically add tool calling support if not present
                self._bot = add_openai_compatible_support(self._bot)
            
            # Log bot info
            bot_name = type(self._bot).__name__
        return self._bot

    def call(self, request: LLMRequest):
        """
        Call the model using COW's bot infrastructure
        """
        try:
            # For non-streaming calls, we'll use the existing reply method
            # This is a simplified implementation
            if hasattr(self.bot, 'call_with_tools'):
                # Use tool-enabled call if available
                kwargs = {
                    'messages': request.messages,
                    'tools': getattr(request, 'tools', None),
                    'stream': False,
                    'model': self.model  # Pass model parameter
                }
                # Only pass max_tokens if it's explicitly set
                if request.max_tokens is not None:
                    kwargs['max_tokens'] = request.max_tokens
                
                # Extract system prompt if present
                system_prompt = getattr(request, 'system', None)
                if system_prompt:
                    kwargs['system'] = system_prompt
                
                response = self.bot.call_with_tools(**kwargs)
                return self._format_response(response)
            else:
                # Fallback to regular call
                # This would need to be implemented based on your specific needs
                raise NotImplementedError("Regular call not implemented yet")
                
        except Exception as e:
            logger.error(f"AgentLLMModel call error: {e}")
            raise
    
    def call_stream(self, request: LLMRequest):
        """
        Call the model with streaming using COW's bot infrastructure
        """
        try:
            if hasattr(self.bot, 'call_with_tools'):
                # Use tool-enabled streaming call if available
                # Ensure max_tokens is an integer, use default if None
                max_tokens = request.max_tokens if request.max_tokens is not None else 4096
                
                # Extract system prompt if present
                system_prompt = getattr(request, 'system', None)
                
                # Build kwargs for call_with_tools
                kwargs = {
                    'messages': request.messages,
                    'tools': getattr(request, 'tools', None),
                    'stream': True,
                    'max_tokens': max_tokens,
                    'model': self.model  # Pass model parameter
                }
                
                # Add system prompt if present
                if system_prompt:
                    kwargs['system'] = system_prompt
                
                stream = self.bot.call_with_tools(**kwargs)
                
                # Convert stream format to our expected format
                for chunk in stream:
                    yield self._format_stream_chunk(chunk)
            else:
                bot_type = type(self.bot).__name__
                raise NotImplementedError(f"Bot {bot_type} does not support call_with_tools. Please add the method.")
                
        except Exception as e:
            logger.error(f"AgentLLMModel call_stream error: {e}", exc_info=True)
            raise
    
    def _format_response(self, response):
        """Format Claude response to our expected format"""
        # This would need to be implemented based on Claude's response format
        return response
    
    def _format_stream_chunk(self, chunk):
        """Format Claude stream chunk to our expected format"""
        # This would need to be implemented based on Claude's stream format
        return chunk


class AgentBridge:
    """
    Bridge class that integrates single super Agent with COW
    """
    
    def __init__(self, bridge: Bridge):
        self.bridge = bridge
        self.agent: Optional[Agent] = None
    
    def create_agent(self, system_prompt: str, tools: List = None, **kwargs) -> Agent:
        """
        Create the super agent with COW integration
        
        Args:
            system_prompt: System prompt
            tools: List of tools (optional)
            **kwargs: Additional agent parameters
            
        Returns:
            Agent instance
        """
        # Create LLM model that uses COW's bot infrastructure
        model = AgentLLMModel(self.bridge)
        
        # Default tools if none provided
        if tools is None:
            # Use ToolManager to load all available tools
            from agent.tools import ToolManager
            tool_manager = ToolManager()
            tool_manager.load_tools()
            
            tools = []
            for tool_name in tool_manager.tool_classes.keys():
                try:
                    tool = tool_manager.create_tool(tool_name)
                    if tool:
                        tools.append(tool)
                except Exception as e:
                    logger.warning(f"[AgentBridge] Failed to load tool {tool_name}: {e}")
        
        # Create the single super agent
        self.agent = Agent(
            system_prompt=system_prompt,
            description=kwargs.get("description", "AI Super Agent"),
            model=model,
            tools=tools,
            max_steps=kwargs.get("max_steps", 15),
            output_mode=kwargs.get("output_mode", "logger"),
            workspace_dir=kwargs.get("workspace_dir"),  # Pass workspace for skills loading
            enable_skills=kwargs.get("enable_skills", True),  # Enable skills by default
            memory_manager=kwargs.get("memory_manager"),  # Pass memory manager
            max_context_tokens=kwargs.get("max_context_tokens"),
            context_reserve_tokens=kwargs.get("context_reserve_tokens")
        )

        # Log skill loading details
        if self.agent.skill_manager:
            logger.info(f"[AgentBridge] SkillManager initialized:")
            logger.info(f"[AgentBridge]   - Managed dir: {self.agent.skill_manager.managed_skills_dir}")
            logger.info(f"[AgentBridge]   - Workspace dir: {self.agent.skill_manager.workspace_dir}")
            logger.info(f"[AgentBridge]   - Total skills: {len(self.agent.skill_manager.skills)}")
            for skill_name in self.agent.skill_manager.skills.keys():
                logger.info(f"[AgentBridge]     * {skill_name}")

        return self.agent
    
    def get_agent(self) -> Optional[Agent]:
        """Get the super agent, create if not exists"""
        if self.agent is None:
            self._init_default_agent()
        return self.agent
    
    def _init_default_agent(self):
        """Initialize default super agent with new prompt system"""
        from config import conf
        import os

        # Get workspace from config
        workspace_root = os.path.expanduser(conf().get("agent_workspace", "~/cow"))

        # Initialize workspace and create template files
        from agent.prompt import ensure_workspace, load_context_files, PromptBuilder

        workspace_files = ensure_workspace(workspace_root, create_templates=True)
        logger.info(f"[AgentBridge] Workspace initialized at: {workspace_root}")

        # Setup memory system
        memory_manager = None
        memory_tools = []

        try:
            # Try to initialize memory system
            from agent.memory import MemoryManager, MemoryConfig
            from agent.tools import MemorySearchTool, MemoryGetTool

            memory_config = MemoryConfig(
                workspace_root=workspace_root,
                embedding_provider="local",  # Use local embedding (no API key needed)
                embedding_model="all-MiniLM-L6-v2"
            )
            
            # Create memory manager with the config
            memory_manager = MemoryManager(memory_config)
            
            # Create memory tools
            memory_tools = [
                MemorySearchTool(memory_manager),
                MemoryGetTool(memory_manager)
            ]
            
            logger.info(f"[AgentBridge] Memory system initialized")
            
        except Exception as e:
            logger.warning(f"[AgentBridge] Memory system not available: {e}")
            logger.info("[AgentBridge] Continuing without memory features")

        # Use ToolManager to dynamically load all available tools
        from agent.tools import ToolManager
        tool_manager = ToolManager()
        tool_manager.load_tools()

        # Create tool instances for all available tools
        tools = []
        file_config = {
            "cwd": workspace_root,
            "memory_manager": memory_manager
        } if memory_manager else {"cwd": workspace_root}

        for tool_name in tool_manager.tool_classes.keys():
            try:
                tool = tool_manager.create_tool(tool_name)
                if tool:
                    # Apply workspace config to file operation tools
                    if tool_name in ['read', 'write', 'edit', 'bash', 'grep', 'find', 'ls']:
                        tool.config = file_config
                        tool.cwd = file_config.get("cwd", tool.cwd if hasattr(tool, 'cwd') else None)
                        if 'memory_manager' in file_config:
                            tool.memory_manager = file_config['memory_manager']
                    tools.append(tool)
                    logger.debug(f"[AgentBridge] Loaded tool: {tool_name}")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to load tool {tool_name}: {e}")

        # Add memory tools
        if memory_tools:
            tools.extend(memory_tools)
            logger.info(f"[AgentBridge] Added {len(memory_tools)} memory tools")

        logger.info(f"[AgentBridge] Loaded {len(tools)} tools: {[t.name for t in tools]}")

        # Load context files (SOUL.md, USER.md, etc.)
        context_files = load_context_files(workspace_root)
        logger.info(f"[AgentBridge] Loaded {len(context_files)} context files: {[f.path for f in context_files]}")

        # Build system prompt using new prompt builder
        prompt_builder = PromptBuilder(
            workspace_dir=workspace_root,
            language="zh"
        )

        # Get runtime info
        runtime_info = {
            "model": conf().get("model", "unknown"),
            "workspace": workspace_root,
            "channel": conf().get("channel_type", "unknown")  # Get from config
        }

        system_prompt = prompt_builder.build(
            tools=tools,
            context_files=context_files,
            memory_manager=memory_manager,
            runtime_info=runtime_info
        )

        logger.info("[AgentBridge] System prompt built successfully")

        # Create agent with configured tools and workspace
        agent = self.create_agent(
            system_prompt=system_prompt,
            tools=tools,
            max_steps=50,
            output_mode="logger",
            workspace_dir=workspace_root,  # Pass workspace to agent for skills loading
            enable_skills=True  # Enable skills auto-loading
        )

        # Attach memory manager to agent if available
        if memory_manager:
            agent.memory_manager = memory_manager
            logger.info(f"[AgentBridge] Memory manager attached to agent")
    
    def agent_reply(self, query: str, context: Context = None, 
                   on_event=None, clear_history: bool = False) -> Reply:
        """
        Use super agent to reply to a query
        
        Args:
            query: User query
            context: COW context (optional)
            on_event: Event callback (optional)
            clear_history: Whether to clear conversation history
            
        Returns:
            Reply object
        """
        try:
            # Get agent (will auto-initialize if needed)
            agent = self.get_agent()
            if not agent:
                return Reply(ReplyType.ERROR, "Failed to initialize super agent")
            
            # Use agent's run_stream method
            response = agent.run_stream(
                user_message=query,
                on_event=on_event,
                clear_history=clear_history
            )
            
            return Reply(ReplyType.TEXT, response)
            
        except Exception as e:
            logger.error(f"Agent reply error: {e}")
            return Reply(ReplyType.ERROR, f"Agent error: {str(e)}")