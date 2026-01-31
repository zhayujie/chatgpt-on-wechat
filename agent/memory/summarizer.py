"""
Memory flush manager

Triggers memory flush before context compaction (similar to clawdbot)
"""

from typing import Optional, Callable, Any
from pathlib import Path
from datetime import datetime


class MemoryFlushManager:
    """
    Manages memory flush operations before context compaction
    
    Similar to clawdbot's memory flush mechanism:
    - Triggers when context approaches token limit
    - Runs a silent agent turn to write memories to disk
    - Uses memory/YYYY-MM-DD.md for daily notes
    - Uses MEMORY.md (workspace root) for long-term curated memories
    """
    
    def __init__(
        self,
        workspace_dir: Path,
        llm_model: Optional[Any] = None
    ):
        """
        Initialize memory flush manager
        
        Args:
            workspace_dir: Workspace directory
            llm_model: LLM model for agent execution (optional)
        """
        self.workspace_dir = workspace_dir
        self.llm_model = llm_model
        
        self.memory_dir = workspace_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Tracking
        self.last_flush_token_count: Optional[int] = None
        self.last_flush_timestamp: Optional[datetime] = None
    
    def should_flush(
        self,
        current_tokens: int,
        context_window: int,
        reserve_tokens: int = 20000,
        soft_threshold: int = 4000
    ) -> bool:
        """
        Determine if memory flush should be triggered
        
        Similar to clawdbot's shouldRunMemoryFlush logic:
        threshold = contextWindow - reserveTokens - softThreshold
        
        Args:
            current_tokens: Current session token count
            context_window: Model's context window size
            reserve_tokens: Reserve tokens for compaction overhead
            soft_threshold: Trigger flush N tokens before threshold
            
        Returns:
            True if flush should run
        """
        if current_tokens <= 0:
            return False
        
        threshold = max(0, context_window - reserve_tokens - soft_threshold)
        if threshold <= 0:
            return False
        
        # Check if we've crossed the threshold
        if current_tokens < threshold:
            return False
        
        # Avoid duplicate flush in same compaction cycle
        if self.last_flush_token_count is not None:
            if current_tokens <= self.last_flush_token_count + soft_threshold:
                return False
        
        return True
    
    def get_today_memory_file(self, user_id: Optional[str] = None) -> Path:
        """
        Get today's memory file path: memory/YYYY-MM-DD.md
        
        Args:
            user_id: Optional user ID for user-specific memory
            
        Returns:
            Path to today's memory file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user_id:
            user_dir = self.memory_dir / "users" / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir / f"{today}.md"
        else:
            return self.memory_dir / f"{today}.md"
    
    def get_main_memory_file(self, user_id: Optional[str] = None) -> Path:
        """
        Get main memory file path: MEMORY.md (workspace root)
        
        Args:
            user_id: Optional user ID for user-specific memory
            
        Returns:
            Path to main memory file
        """
        if user_id:
            user_dir = self.memory_dir / "users" / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir / "MEMORY.md"
        else:
            # Return workspace root MEMORY.md
            return Path(self.workspace_dir) / "MEMORY.md"
    
    def create_flush_prompt(self) -> str:
        """
        Create prompt for memory flush turn
        
        Similar to clawdbot's DEFAULT_MEMORY_FLUSH_PROMPT
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return (
            f"Pre-compaction memory flush. "
            f"Store durable memories now (use memory/{today}.md for daily notes; "
            f"create memory/ if needed). "
            f"If nothing to store, reply with NO_REPLY."
        )
    
    def create_flush_system_prompt(self) -> str:
        """
        Create system prompt for memory flush turn
        
        Similar to clawdbot's DEFAULT_MEMORY_FLUSH_SYSTEM_PROMPT
        """
        return (
            "Pre-compaction memory flush turn. "
            "The session is near auto-compaction; capture durable memories to disk. "
            "You may reply, but usually NO_REPLY is correct."
        )
    
    async def execute_flush(
        self,
        agent_executor: Callable,
        current_tokens: int,
        user_id: Optional[str] = None,
        **executor_kwargs
    ) -> bool:
        """
        Execute memory flush by running a silent agent turn
        
        Args:
            agent_executor: Function to execute agent with prompt
            current_tokens: Current token count
            user_id: Optional user ID
            **executor_kwargs: Additional kwargs for agent executor
            
        Returns:
            True if flush completed successfully
        """
        try:
            # Create flush prompts
            prompt = self.create_flush_prompt()
            system_prompt = self.create_flush_system_prompt()
            
            # Execute agent turn (silent, no user-visible reply expected)
            await agent_executor(
                prompt=prompt,
                system_prompt=system_prompt,
                silent=True,  # NO_REPLY expected
                **executor_kwargs
            )
            
            # Track flush
            self.last_flush_token_count = current_tokens
            self.last_flush_timestamp = datetime.now()
            
            return True
            
        except Exception as e:
            print(f"Memory flush failed: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get memory flush status"""
        return {
            'last_flush_tokens': self.last_flush_token_count,
            'last_flush_time': self.last_flush_timestamp.isoformat() if self.last_flush_timestamp else None,
            'today_file': str(self.get_today_memory_file()),
            'main_file': str(self.get_main_memory_file())
        }


def create_memory_files_if_needed(workspace_dir: Path, user_id: Optional[str] = None):
    """
    Create default memory files if they don't exist
    
    Args:
        workspace_dir: Workspace directory
        user_id: Optional user ID for user-specific files
    """
    memory_dir = workspace_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main MEMORY.md in workspace root
    if user_id:
        user_dir = memory_dir / "users" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        main_memory = user_dir / "MEMORY.md"
    else:
        main_memory = Path(workspace_dir) / "MEMORY.md"
    
    if not main_memory.exists():
        # Create empty file or with minimal structure (no obvious "Memory" header)
        # Following clawdbot's approach: memories should blend naturally into context
        main_memory.write_text("")
    
    # Create today's memory file
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id:
        user_dir = memory_dir / "users" / user_id
        today_memory = user_dir / f"{today}.md"
    else:
        today_memory = memory_dir / f"{today}.md"
    
    if not today_memory.exists():
        today_memory.write_text(
            f"# Daily Memory: {today}\n\n"
            f"Day-to-day notes and running context.\n\n"
        )
