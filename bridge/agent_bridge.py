"""
Agent Bridge - Integrates Agent system with existing COW bridge
"""

from typing import Optional, List

from agent.protocol import Agent, LLMModel, LLMRequest
from models.openai_compatible_bot import OpenAICompatibleBot
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
    Bridge class that integrates super Agent with COW
    Manages multiple agent instances per session for conversation isolation
    """
    
    def __init__(self, bridge: Bridge):
        self.bridge = bridge
        self.agents = {}  # session_id -> Agent instance mapping
        self.default_agent = None  # For backward compatibility (no session_id)
        self.agent: Optional[Agent] = None
        self.scheduler_initialized = False
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
        
        # Create agent instance
        agent = Agent(
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
        if agent.skill_manager:
            logger.info(f"[AgentBridge] SkillManager initialized:")
            logger.info(f"[AgentBridge]   - Managed dir: {agent.skill_manager.managed_skills_dir}")
            logger.info(f"[AgentBridge]   - Workspace dir: {agent.skill_manager.workspace_dir}")
            logger.info(f"[AgentBridge]   - Total skills: {len(agent.skill_manager.skills)}")
            for skill_name in agent.skill_manager.skills.keys():
                logger.info(f"[AgentBridge]     * {skill_name}")

        return agent
    
    def get_agent(self, session_id: str = None) -> Optional[Agent]:
        """
        Get agent instance for the given session
        
        Args:
            session_id: Session identifier (e.g., user_id). If None, returns default agent.
        
        Returns:
            Agent instance for this session
        """
        # If no session_id, use default agent (backward compatibility)
        if session_id is None:
            if self.default_agent is None:
                self._init_default_agent()
            return self.default_agent
        
        # Check if agent exists for this session
        if session_id not in self.agents:
            logger.info(f"[AgentBridge] Creating new agent for session: {session_id}")
            self._init_agent_for_session(session_id)
        
        return self.agents[session_id]
    
    def _init_default_agent(self):
        """Initialize default super agent with new prompt system"""
        from config import conf
        import os

        # Get workspace from config
        workspace_root = os.path.expanduser(conf().get("agent_workspace", "~/cow"))

        # Load environment variables from workspace .env file
        env_file = os.path.join(workspace_root, '.env')
        if os.path.exists(env_file):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file, override=True)
                logger.info(f"[AgentBridge] Loaded environment variables from {env_file}")
            except ImportError:
                logger.warning("[AgentBridge] python-dotenv not installed, skipping .env file loading")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to load .env file: {e}")
        
        # Migrate API keys from config.json to environment variables (if not already set)
        self._migrate_config_to_env(workspace_root)

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

            # 从 config.json 读取 OpenAI 配置
            openai_api_key = conf().get("open_ai_api_key", "")
            openai_api_base = conf().get("open_ai_api_base", "")
            
            # 尝试初始化 OpenAI embedding provider
            embedding_provider = None
            if openai_api_key:
                try:
                    from agent.memory import create_embedding_provider
                    embedding_provider = create_embedding_provider(
                        provider="openai",
                        model="text-embedding-3-small",
                        api_key=openai_api_key,
                        api_base=openai_api_base or "https://api.openai.com/v1"
                    )
                    logger.info(f"[AgentBridge] OpenAI embedding initialized")
                except Exception as embed_error:
                    logger.warning(f"[AgentBridge] OpenAI embedding failed: {embed_error}")
                    logger.info(f"[AgentBridge] Using keyword-only search")
            else:
                logger.info(f"[AgentBridge] No OpenAI API key, using keyword-only search")
            
            # 创建 memory config
            memory_config = MemoryConfig(workspace_root=workspace_root)
            
            # 创建 memory manager
            memory_manager = MemoryManager(memory_config, embedding_provider=embedding_provider)
            
            # 初始化时执行一次 sync，确保数据库有数据
            import asyncio
            try:
                # 尝试在当前事件循环中执行
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.create_task(memory_manager.sync())
                    logger.info("[AgentBridge] Memory sync scheduled")
                else:
                    # 如果没有运行的循环，直接执行
                    loop.run_until_complete(memory_manager.sync())
                    logger.info("[AgentBridge] Memory synced successfully")
            except RuntimeError:
                # 没有事件循环，创建新的
                asyncio.run(memory_manager.sync())
                logger.info("[AgentBridge] Memory synced successfully")
            except Exception as e:
                logger.warning(f"[AgentBridge] Memory sync failed: {e}")
            
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
                # Special handling for EnvConfig tool - pass agent_bridge reference
                if tool_name == "env_config":
                    from agent.tools import EnvConfig
                    tool = EnvConfig({
                        "workspace_dir": workspace_root,
                        "agent_bridge": self  # Pass self reference for hot reload
                    })
                else:
                    tool = tool_manager.create_tool(tool_name)
                
                if tool:
                    # Apply workspace config to file operation tools
                    if tool_name in ['read', 'write', 'edit', 'bash', 'grep', 'find', 'ls']:
                        tool.config = file_config
                        tool.cwd = file_config.get("cwd", tool.cwd if hasattr(tool, 'cwd') else None)
                        if 'memory_manager' in file_config:
                            tool.memory_manager = file_config['memory_manager']
                    # Apply API key for bocha_search tool
                    elif tool_name == 'bocha_search':
                        bocha_api_key = conf().get("bocha_api_key", "")
                        if bocha_api_key:
                            tool.config = {"bocha_api_key": bocha_api_key}
                            tool.api_key = bocha_api_key
                    tools.append(tool)
                    logger.debug(f"[AgentBridge] Loaded tool: {tool_name}")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to load tool {tool_name}: {e}")

        # Add memory tools
        if memory_tools:
            tools.extend(memory_tools)
            logger.info(f"[AgentBridge] Added {len(memory_tools)} memory tools")

        # Initialize scheduler service (once)
        if not self.scheduler_initialized:
            try:
                from agent.tools.scheduler.integration import init_scheduler
                if init_scheduler(self):
                    self.scheduler_initialized = True
                    logger.info("[AgentBridge] Scheduler service initialized")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to initialize scheduler: {e}")
        
        # Inject scheduler dependencies into SchedulerTool instances
        if self.scheduler_initialized:
            try:
                from agent.tools.scheduler.integration import get_task_store, get_scheduler_service
                from agent.tools import SchedulerTool
                
                task_store = get_task_store()
                scheduler_service = get_scheduler_service()
                
                for tool in tools:
                    if isinstance(tool, SchedulerTool):
                        tool.task_store = task_store
                        tool.scheduler_service = scheduler_service
                        if not tool.config:
                            tool.config = {}
                        tool.config["channel_type"] = conf().get("channel_type", "unknown")
                        logger.debug("[AgentBridge] Injected scheduler dependencies into SchedulerTool")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to inject scheduler dependencies: {e}")

        logger.info(f"[AgentBridge] Loaded {len(tools)} tools: {[t.name for t in tools]}")

        # Load context files (SOUL.md, USER.md, etc.)
        context_files = load_context_files(workspace_root)
        logger.info(f"[AgentBridge] Loaded {len(context_files)} context files: {[f.path for f in context_files]}")

        # Check if this is the first conversation
        from agent.prompt.workspace import is_first_conversation, mark_conversation_started
        is_first = is_first_conversation(workspace_root)
        if is_first:
            logger.info("[AgentBridge] First conversation detected")
        
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
            runtime_info=runtime_info,
            is_first_conversation=is_first
        )
        
        # Mark conversation as started (will be saved after first user message)
        if is_first:
            mark_conversation_started(workspace_root)

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
        
        # Store as default agent
        self.default_agent = agent
    
    def _init_agent_for_session(self, session_id: str):
        """
        Initialize agent for a specific session
        Reuses the same configuration as default agent
        """
        from config import conf
        import os

        # Get workspace from config
        workspace_root = os.path.expanduser(conf().get("agent_workspace", "~/cow"))

        # Load environment variables from workspace .env file
        env_file = os.path.join(workspace_root, '.env')
        if os.path.exists(env_file):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file, override=True)
                logger.info(f"[AgentBridge] Loaded environment variables from {env_file} for session {session_id}")
            except ImportError:
                logger.warning(f"[AgentBridge] python-dotenv not installed, skipping .env file loading for session {session_id}")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to load .env file for session {session_id}: {e}")
        
        # Migrate API keys from config.json to environment variables (if not already set)
        self._migrate_config_to_env(workspace_root)

        # Initialize workspace
        from agent.prompt import ensure_workspace, load_context_files, PromptBuilder

        workspace_files = ensure_workspace(workspace_root, create_templates=True)

        # Setup memory system
        memory_manager = None
        memory_tools = []

        try:
            from agent.memory import MemoryManager, MemoryConfig, create_embedding_provider
            from agent.tools import MemorySearchTool, MemoryGetTool

            # 从 config.json 读取 OpenAI 配置
            openai_api_key = conf().get("open_ai_api_key", "")
            openai_api_base = conf().get("open_ai_api_base", "")
            
            # 尝试初始化 OpenAI embedding provider
            embedding_provider = None
            if openai_api_key:
                try:
                    embedding_provider = create_embedding_provider(
                        provider="openai",
                        model="text-embedding-3-small",
                        api_key=openai_api_key,
                        api_base=openai_api_base or "https://api.openai.com/v1"
                    )
                    logger.info(f"[AgentBridge] OpenAI embedding initialized for session {session_id}")
                except Exception as embed_error:
                    logger.warning(f"[AgentBridge] OpenAI embedding failed for session {session_id}: {embed_error}")
                    logger.info(f"[AgentBridge] Using keyword-only search for session {session_id}")
            else:
                logger.info(f"[AgentBridge] No OpenAI API key, using keyword-only search for session {session_id}")
            
            # 创建 memory config
            memory_config = MemoryConfig(workspace_root=workspace_root)
            
            # 创建 memory manager
            memory_manager = MemoryManager(memory_config, embedding_provider=embedding_provider)
            
            # 初始化时执行一次 sync，确保数据库有数据
            import asyncio
            try:
                # 尝试在当前事件循环中执行
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，创建任务
                    asyncio.create_task(memory_manager.sync())
                    logger.info(f"[AgentBridge] Memory sync scheduled for session {session_id}")
                else:
                    # 如果没有运行的循环，直接执行
                    loop.run_until_complete(memory_manager.sync())
                    logger.info(f"[AgentBridge] Memory synced successfully for session {session_id}")
            except RuntimeError:
                # 没有事件循环，创建新的
                asyncio.run(memory_manager.sync())
                logger.info(f"[AgentBridge] Memory synced successfully for session {session_id}")
            except Exception as sync_error:
                logger.warning(f"[AgentBridge] Memory sync failed for session {session_id}: {sync_error}")
            
            memory_tools = [
                MemorySearchTool(memory_manager),
                MemoryGetTool(memory_manager)
            ]
            
        except Exception as e:
            logger.warning(f"[AgentBridge] Memory system not available for session {session_id}: {e}")
            import traceback
            logger.warning(f"[AgentBridge] Memory init traceback: {traceback.format_exc()}")

        # Load tools
        from agent.tools import ToolManager
        tool_manager = ToolManager()
        tool_manager.load_tools()

        tools = []
        file_config = {
            "cwd": workspace_root,
            "memory_manager": memory_manager
        } if memory_manager else {"cwd": workspace_root}

        for tool_name in tool_manager.tool_classes.keys():
            try:
                tool = tool_manager.create_tool(tool_name)
                if tool:
                    if tool_name in ['read', 'write', 'edit', 'bash', 'grep', 'find', 'ls']:
                        tool.config = file_config
                        tool.cwd = file_config.get("cwd", tool.cwd if hasattr(tool, 'cwd') else None)
                        if 'memory_manager' in file_config:
                            tool.memory_manager = file_config['memory_manager']
                    elif tool_name == 'bocha_search':
                        bocha_api_key = conf().get("bocha_api_key", "")
                        if bocha_api_key:
                            tool.config = {"bocha_api_key": bocha_api_key}
                            tool.api_key = bocha_api_key
                    tools.append(tool)
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to load tool {tool_name} for session {session_id}: {e}")

        if memory_tools:
            tools.extend(memory_tools)
        
        # Initialize scheduler service (once, if not already initialized)
        if not self.scheduler_initialized:
            try:
                from agent.tools.scheduler.integration import init_scheduler
                if init_scheduler(self):
                    self.scheduler_initialized = True
                    logger.info(f"[AgentBridge] Scheduler service initialized for session {session_id}")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to initialize scheduler for session {session_id}: {e}")
        
        # Inject scheduler dependencies into SchedulerTool instances
        if self.scheduler_initialized:
            try:
                from agent.tools.scheduler.integration import get_task_store, get_scheduler_service
                from agent.tools import SchedulerTool
                
                task_store = get_task_store()
                scheduler_service = get_scheduler_service()
                
                for tool in tools:
                    if isinstance(tool, SchedulerTool):
                        tool.task_store = task_store
                        tool.scheduler_service = scheduler_service
                        if not tool.config:
                            tool.config = {}
                        tool.config["channel_type"] = conf().get("channel_type", "unknown")
                        logger.debug(f"[AgentBridge] Injected scheduler dependencies for session {session_id}")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to inject scheduler dependencies for session {session_id}: {e}")

        # Load context files
        context_files = load_context_files(workspace_root)

        # Initialize skill manager
        skill_manager = None
        try:
            from agent.skills import SkillManager
            skill_manager = SkillManager(workspace_dir=workspace_root)
            logger.info(f"[AgentBridge] Initialized SkillManager with {len(skill_manager.skills)} skills for session {session_id}")
        except Exception as e:
            logger.warning(f"[AgentBridge] Failed to initialize SkillManager for session {session_id}: {e}")

        # Check if this is the first conversation
        from agent.prompt.workspace import is_first_conversation, mark_conversation_started
        is_first = is_first_conversation(workspace_root)
        
        # Build system prompt
        prompt_builder = PromptBuilder(
            workspace_dir=workspace_root,
            language="zh"
        )

        # Get current time and timezone info
        import datetime
        import time
        
        now = datetime.datetime.now()
        
        # Get timezone info
        try:
            offset = -time.timezone if not time.daylight else -time.altzone
            hours = offset // 3600
            minutes = (offset % 3600) // 60
            if minutes:
                timezone_name = f"UTC{hours:+03d}:{minutes:02d}"
            else:
                timezone_name = f"UTC{hours:+03d}"
        except Exception:
            timezone_name = "UTC"
        
        # Chinese weekday mapping
        weekday_map = {
            'Monday': '星期一',
            'Tuesday': '星期二',
            'Wednesday': '星期三',
            'Thursday': '星期四',
            'Friday': '星期五',
            'Saturday': '星期六',
            'Sunday': '星期日'
        }
        weekday_zh = weekday_map.get(now.strftime("%A"), now.strftime("%A"))
        
        runtime_info = {
            "model": conf().get("model", "unknown"),
            "workspace": workspace_root,
            "channel": conf().get("channel_type", "unknown"),
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": weekday_zh,
            "timezone": timezone_name
        }

        system_prompt = prompt_builder.build(
            tools=tools,
            context_files=context_files,
            skill_manager=skill_manager,
            memory_manager=memory_manager,
            runtime_info=runtime_info,
            is_first_conversation=is_first
        )
        
        if is_first:
            mark_conversation_started(workspace_root)

        # Create agent for this session
        agent = self.create_agent(
            system_prompt=system_prompt,
            tools=tools,
            max_steps=50,
            output_mode="logger",
            workspace_dir=workspace_root,
            skill_manager=skill_manager,
            enable_skills=True
        )

        if memory_manager:
            agent.memory_manager = memory_manager
        
        # Store agent for this session
        self.agents[session_id] = agent
        logger.info(f"[AgentBridge] Agent created for session: {session_id}")
    
    def agent_reply(self, query: str, context: Context = None, 
                   on_event=None, clear_history: bool = False) -> Reply:
        """
        Use super agent to reply to a query
        
        Args:
            query: User query
            context: COW context (optional, contains session_id for user isolation)
            on_event: Event callback (optional)
            clear_history: Whether to clear conversation history
            
        Returns:
            Reply object
        """
        try:
            # Extract session_id from context for user isolation
            session_id = None
            if context:
                session_id = context.kwargs.get("session_id") or context.get("session_id")
            
            # Get agent for this session (will auto-initialize if needed)
            agent = self.get_agent(session_id=session_id)
            if not agent:
                return Reply(ReplyType.ERROR, "Failed to initialize super agent")
            
            # Attach context to scheduler tool if present
            if context and agent.tools:
                for tool in agent.tools:
                    if tool.name == "scheduler":
                        try:
                            from agent.tools.scheduler.integration import attach_scheduler_to_tool
                            attach_scheduler_to_tool(tool, context)
                        except Exception as e:
                            logger.warning(f"[AgentBridge] Failed to attach context to scheduler: {e}")
                        break
            
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
    
    def _migrate_config_to_env(self, workspace_root: str):
        """
        Migrate API keys from config.json to .env file if not already set
        
        Args:
            workspace_root: Workspace directory path
        """
        from config import conf
        import os
        
        # Mapping from config.json keys to environment variable names
        key_mapping = {
            "open_ai_api_key": "OPENAI_API_KEY",
            "open_ai_api_base": "OPENAI_API_BASE",
            "gemini_api_key": "GEMINI_API_KEY",
            "claude_api_key": "CLAUDE_API_KEY",
            "linkai_api_key": "LINKAI_API_KEY",
        }
        
        env_file = os.path.join(workspace_root, '.env')
        
        # Read existing env vars from .env file
        existing_env_vars = {}
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, _ = line.split('=', 1)
                            existing_env_vars[key.strip()] = True
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to read .env file: {e}")
        
        # Check which keys need to be migrated
        keys_to_migrate = {}
        for config_key, env_key in key_mapping.items():
            # Skip if already in .env file
            if env_key in existing_env_vars:
                continue
            
            # Get value from config.json
            value = conf().get(config_key, "")
            if value and value.strip():  # Only migrate non-empty values
                keys_to_migrate[env_key] = value.strip()
        
        # Write new keys to .env file
        if keys_to_migrate:
            try:
                # Ensure .env file exists
                if not os.path.exists(env_file):
                    os.makedirs(os.path.dirname(env_file), exist_ok=True)
                    open(env_file, 'a').close()
                
                # Append new keys
                with open(env_file, 'a', encoding='utf-8') as f:
                    f.write('\n# Auto-migrated from config.json\n')
                    for key, value in keys_to_migrate.items():
                        f.write(f'{key}={value}\n')
                        # Also set in current process
                        os.environ[key] = value
                
                logger.info(f"[AgentBridge] Migrated {len(keys_to_migrate)} API keys from config.json to .env: {list(keys_to_migrate.keys())}")
            except Exception as e:
                logger.warning(f"[AgentBridge] Failed to migrate API keys: {e}")
    
    def clear_session(self, session_id: str):
        """
        Clear a specific session's agent and conversation history
        
        Args:
            session_id: Session identifier to clear
        """
        if session_id in self.agents:
            logger.info(f"[AgentBridge] Clearing session: {session_id}")
            del self.agents[session_id]
    
    def clear_all_sessions(self):
        """Clear all agent sessions"""
        logger.info(f"[AgentBridge] Clearing all sessions ({len(self.agents)} total)")
        self.agents.clear()
        self.default_agent = None
    
    def refresh_all_skills(self) -> int:
        """
        Refresh skills in all agent instances after environment variable changes.
        This allows hot-reload of skills without restarting the agent.
        
        Returns:
            Number of agent instances refreshed
        """
        import os
        from dotenv import load_dotenv
        from config import conf
        
        # Reload environment variables from .env file
        workspace_root = os.path.expanduser(conf().get("agent_workspace", "~/cow"))
        env_file = os.path.join(workspace_root, '.env')
        
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            logger.info(f"[AgentBridge] Reloaded environment variables from {env_file}")
        
        refreshed_count = 0
        
        # Refresh default agent
        if self.default_agent and hasattr(self.default_agent, 'skill_manager'):
            self.default_agent.skill_manager.refresh_skills()
            refreshed_count += 1
            logger.info("[AgentBridge] Refreshed skills in default agent")
        
        # Refresh all session agents
        for session_id, agent in self.agents.items():
            if hasattr(agent, 'skill_manager'):
                agent.skill_manager.refresh_skills()
                refreshed_count += 1
        
        if refreshed_count > 0:
            logger.info(f"[AgentBridge] Refreshed skills in {refreshed_count} agent instance(s)")
        
        return refreshed_count