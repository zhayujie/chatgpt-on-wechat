"""
Agent Bridge - Integrates Agent system with existing COW bridge
"""

from typing import Optional, List

from agent.protocol import Agent, LLMModel, LLMRequest
from agent.tools import Calculator, CurrentTime, Read, Write, Edit, Bash, Grep, Find, Ls
from bridge.bridge import Bridge
from bridge.context import Context
from bridge.reply import Reply, ReplyType
from common import const
from common.log import logger


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
    
    @property
    def bot(self):
        """Lazy load the bot"""
        if self._bot is None:
            self._bot = self.bridge.get_bot(self.bot_type)
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
                    'stream': False
                }
                # Only pass max_tokens if it's explicitly set
                if request.max_tokens is not None:
                    kwargs['max_tokens'] = request.max_tokens
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
                    'max_tokens': max_tokens
                }
                
                # Add system prompt if present
                if system_prompt:
                    kwargs['system'] = system_prompt
                
                stream = self.bot.call_with_tools(**kwargs)
                
                # Convert Claude stream format to our expected format
                for chunk in stream:
                    yield self._format_stream_chunk(chunk)
            else:
                raise NotImplementedError("Streaming call not implemented yet")
                
        except Exception as e:
            logger.error(f"AgentLLMModel call_stream error: {e}")
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
            tools = [
                Calculator(),
                CurrentTime(),
                Read(),
                Write(),
                Edit(),
                Bash(),
                Grep(),
                Find(),
                Ls()
            ]
        
        # Create the single super agent
        self.agent = Agent(
            system_prompt=system_prompt,
            description=kwargs.get("description", "AI Super Agent"),
            model=model,
            tools=tools,
            max_steps=kwargs.get("max_steps", 15),
            output_mode=kwargs.get("output_mode", "logger")
        )
        
        return self.agent
    
    def get_agent(self) -> Optional[Agent]:
        """Get the super agent, create if not exists"""
        if self.agent is None:
            self._init_default_agent()
        return self.agent
    
    def _init_default_agent(self):
        """Initialize default super agent with config and memory"""
        from config import conf
        import os
        
        # Get base system prompt from config
        base_prompt = conf().get("character_desc", "你是一个AI助手")
        
        # Setup memory if enabled
        memory_manager = None
        memory_tools = []
        
        try:
            # Try to initialize memory system
            from agent.memory import MemoryManager, MemoryConfig
            from agent.tools import MemorySearchTool, MemoryGetTool
            
            # Create memory config directly with sensible defaults
            workspace_root = os.path.expanduser("~/cow")
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
            
            # Build memory guidance and add to system prompt
            memory_guidance = memory_manager.build_memory_guidance(
                lang="zh",
                include_context=True
            )
            system_prompt = base_prompt + "\n\n" + memory_guidance
            
            logger.info(f"[AgentBridge] Memory system initialized")
            logger.info(f"[AgentBridge] Workspace: {memory_config.get_workspace()}")
            
        except Exception as e:
            logger.warning(f"[AgentBridge] Memory system not available: {e}")
            logger.info("[AgentBridge] Continuing without memory features")
            system_prompt = base_prompt
            import traceback
            traceback.print_exc()
        
        logger.info("[AgentBridge] Initializing super agent")
        
        # Configure file tools to work in the correct workspace
        file_config = {"cwd": workspace_root} if memory_manager else {}
        
        # Create default tools with workspace config
        from agent.tools import Calculator, CurrentTime, Read, Write, Edit, Bash, Grep, Find, Ls
        tools = [
            Calculator(),
            CurrentTime(),
            Read(config=file_config),
            Write(config=file_config),
            Edit(config=file_config),
            Bash(config=file_config),
            Grep(config=file_config),
            Find(config=file_config),
            Ls(config=file_config)
        ]
        
        # Create agent with configured tools
        agent = self.create_agent(
            system_prompt=system_prompt,
            tools=tools,
            max_steps=50,
            output_mode="logger"
        )
        
        # Attach memory manager to agent if available
        if memory_manager:
            agent.memory_manager = memory_manager
        
        # Add memory tools if available
        if memory_tools:
            for tool in memory_tools:
                agent.add_tool(tool)
            logger.info(f"[AgentBridge] Added {len(memory_tools)} memory tools")
    
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