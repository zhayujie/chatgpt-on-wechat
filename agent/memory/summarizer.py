"""
Memory flush manager

Handles memory persistence when conversation context is trimmed or overflows:
- Uses LLM to summarize discarded messages into concise key-information entries
- Writes to daily memory files (lazy creation)
- Deduplicates trim flushes to avoid repeated writes
- Runs summarization asynchronously to avoid blocking normal replies
- Provides daily summary interface for scheduler
"""

import threading
from typing import Optional, Callable, Any, List, Dict
from pathlib import Path
from datetime import datetime
from common.log import logger


SUMMARIZE_SYSTEM_PROMPT = """你是一个记忆提取助手。你的任务是从对话记录中提取值得记住的信息，生成简洁的记忆摘要。

输出要求：
1. 以事件/关键信息为维度记录，每条一行，用 "- " 开头
2. 记录有价值的关键信息，例如用户提出的要求及助手的解决方案，对话中涉及的事实信息，用户的偏好、决策或重要结论
3. 每条摘要需要简明扼要，只保留关键信息
4. 直接输出摘要内容，不要加任何前缀说明
5. 当对话没有任何记录价值例如只是简单问候，可回复"无\""""

SUMMARIZE_USER_PROMPT = """请从以下对话记录中提取关键信息，生成记忆摘要：

{conversation}"""


class MemoryFlushManager:
    """
    Manages memory flush operations.
    
    Flush is triggered by agent_stream in two scenarios:
    1. Context trim: _trim_messages discards old turns → flush discarded content
    2. Context overflow: API rejects request → emergency flush before clearing
    
    Additionally, create_daily_summary() can be called by scheduler for end-of-day summaries.
    """
    
    def __init__(
        self,
        workspace_dir: Path,
        llm_model: Optional[Any] = None,
    ):
        self.workspace_dir = workspace_dir
        self.llm_model = llm_model
        
        self.memory_dir = workspace_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.last_flush_timestamp: Optional[datetime] = None
        self._trim_flushed_hashes: set = set()  # Content hashes of already-flushed messages
        self._last_flushed_content_hash: str = ""  # Content hash at last flush, for daily dedup
    
    def get_today_memory_file(self, user_id: Optional[str] = None, ensure_exists: bool = False) -> Path:
        """Get today's memory file path: memory/YYYY-MM-DD.md"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user_id:
            user_dir = self.memory_dir / "users" / user_id
            if ensure_exists:
                user_dir.mkdir(parents=True, exist_ok=True)
            today_file = user_dir / f"{today}.md"
        else:
            today_file = self.memory_dir / f"{today}.md"
        
        if ensure_exists and not today_file.exists():
            today_file.parent.mkdir(parents=True, exist_ok=True)
            today_file.write_text(f"# Daily Memory: {today}\n\n")
        
        return today_file
    
    def get_main_memory_file(self, user_id: Optional[str] = None) -> Path:
        """Get main memory file path: MEMORY.md (workspace root)"""
        if user_id:
            user_dir = self.memory_dir / "users" / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir / "MEMORY.md"
        else:
            return Path(self.workspace_dir) / "MEMORY.md"
    
    def get_status(self) -> dict:
        return {
            'last_flush_time': self.last_flush_timestamp.isoformat() if self.last_flush_timestamp else None,
            'today_file': str(self.get_today_memory_file()),
            'main_file': str(self.get_main_memory_file())
        }

    # ---- Flush execution (called by agent_stream or scheduler) ----
    
    def flush_from_messages(
        self,
        messages: List[Dict],
        user_id: Optional[str] = None,
        reason: str = "trim",
        max_messages: int = 0,
    ) -> bool:
        """
        Asynchronously summarize and flush messages to daily memory.
        
        Deduplication runs synchronously, then LLM summarization + file write
        run in a background thread so the main reply flow is never blocked.
        
        Args:
            messages: Conversation message list (OpenAI/Claude format)
            user_id: Optional user ID for user-scoped memory
            reason: Why flush was triggered ("trim" | "overflow" | "daily_summary")
            max_messages: Max recent messages to summarize (0 = all)
        
        Returns:
            True if flush was dispatched
        """
        try:
            import hashlib
            deduped = []
            for m in messages:
                text = self._extract_text_from_content(m.get("content", ""))
                if not text or not text.strip():
                    continue
                h = hashlib.md5(text.encode("utf-8")).hexdigest()
                if h not in self._trim_flushed_hashes:
                    self._trim_flushed_hashes.add(h)
                    deduped.append(m)
            if not deduped:
                return False
            
            import copy
            snapshot = copy.deepcopy(deduped)
            thread = threading.Thread(
                target=self._flush_worker,
                args=(snapshot, user_id, reason, max_messages),
                daemon=True,
            )
            thread.start()
            logger.info(f"[MemoryFlush] Async flush dispatched (reason={reason}, msgs={len(snapshot)})")
            return True
            
        except Exception as e:
            logger.warning(f"[MemoryFlush] Failed to dispatch flush (reason={reason}): {e}")
            return False

    def _flush_worker(
        self,
        messages: List[Dict],
        user_id: Optional[str],
        reason: str,
        max_messages: int,
    ):
        """Background worker: summarize with LLM and write to daily file."""
        try:
            summary = self._summarize_messages(messages, max_messages)
            if not summary or not summary.strip() or summary.strip() == "无":
                logger.info(f"[MemoryFlush] No valuable content to flush (reason={reason})")
                return
            
            daily_file = ensure_daily_memory_file(self.workspace_dir, user_id)
            
            if reason == "overflow":
                header = f"## Context Overflow Recovery ({datetime.now().strftime('%H:%M')})"
                note = "The following conversation was trimmed due to context overflow:\n"
            elif reason == "trim":
                header = f"## Trimmed Context ({datetime.now().strftime('%H:%M')})"
                note = ""
            elif reason == "daily_summary":
                header = f"## Daily Summary ({datetime.now().strftime('%H:%M')})"
                note = ""
            else:
                header = f"## Session Notes ({datetime.now().strftime('%H:%M')})"
                note = ""
            
            flush_entry = f"\n{header}\n\n{note}{summary}\n"
            
            with open(daily_file, "a", encoding="utf-8") as f:
                f.write(flush_entry)
            
            self.last_flush_timestamp = datetime.now()
            
            logger.info(f"[MemoryFlush] Wrote to {daily_file.name} (reason={reason}, chars={len(summary)})")
            
        except Exception as e:
            logger.warning(f"[MemoryFlush] Async flush failed (reason={reason}): {e}")
    
    def create_daily_summary(
        self,
        messages: List[Dict],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Generate end-of-day summary. Called by daily timer.
        Skips if messages haven't changed since last flush.
        """
        import hashlib
        content = "".join(
            self._extract_text_from_content(m.get("content", ""))
            for m in messages
        )
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        if content_hash == self._last_flushed_content_hash:
            logger.debug("[MemoryFlush] Daily summary skipped: no new content since last flush")
            return False
        self._last_flushed_content_hash = content_hash
        return self.flush_from_messages(
            messages=messages,
            user_id=user_id,
            reason="daily_summary",
            max_messages=0,
        )
    
    # ---- Internal helpers ----
    
    def _summarize_messages(self, messages: List[Dict], max_messages: int = 0) -> str:
        """
        Summarize conversation messages using LLM, with rule-based fallback.
        """
        conversation_text = self._format_conversation_for_summary(messages, max_messages)
        if not conversation_text.strip():
            return ""
        
        # Try LLM summarization first
        if self.llm_model:
            try:
                summary = self._call_llm_for_summary(conversation_text)
                if summary and summary.strip() and summary.strip() != "无":
                    return summary.strip()
            except Exception as e:
                logger.warning(f"[MemoryFlush] LLM summarization failed, using fallback: {e}")
        
        return self._extract_summary_fallback(messages, max_messages)

    def _format_conversation_for_summary(self, messages: List[Dict], max_messages: int = 0) -> str:
        """Format messages into readable conversation text for LLM summarization."""
        msgs = messages if max_messages == 0 else messages[-max_messages * 2:]
        lines = []
        for msg in msgs:
            role = msg.get("role", "")
            text = self._extract_text_from_content(msg.get("content", ""))
            if not text or not text.strip():
                continue
            text = text.strip()
            if role == "user":
                lines.append(f"用户: {text[:500]}")
            elif role == "assistant":
                lines.append(f"助手: {text[:500]}")
        return "\n".join(lines)

    def _call_llm_for_summary(self, conversation_text: str) -> str:
        """Call LLM to generate a concise summary of the conversation."""
        from agent.protocol.models import LLMRequest
        
        request = LLMRequest(
            messages=[{"role": "user", "content": SUMMARIZE_USER_PROMPT.format(conversation=conversation_text)}],
            temperature=0,
            max_tokens=500,
            stream=False,
            system=SUMMARIZE_SYSTEM_PROMPT,
        )
        
        response = self.llm_model.call(request)
        
        if isinstance(response, dict):
            if response.get("error"):
                raise RuntimeError(response.get("message", "LLM call failed"))
            # OpenAI format
            choices = response.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
        
        # Handle response object with attribute access (e.g. OpenAI SDK response)
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content or ""
        
        return ""

    @staticmethod
    def _extract_summary_fallback(messages: List[Dict], max_messages: int = 0) -> str:
        """Rule-based fallback when LLM is unavailable."""
        msgs = messages if max_messages == 0 else messages[-max_messages * 2:]
        
        items = []
        for msg in msgs:
            role = msg.get("role", "")
            text = MemoryFlushManager._extract_text_from_content(msg.get("content", ""))
            if not text or not text.strip():
                continue
            text = text.strip()
            
            if role == "user":
                if len(text) <= 5:
                    continue
                items.append(f"- 用户请求: {text[:200]}")
            elif role == "assistant":
                first_line = text.split("\n")[0].strip()
                if len(first_line) > 10:
                    items.append(f"- 处理结果: {first_line[:200]}")
        
        return "\n".join(items[:15])
    
    @staticmethod
    def _extract_text_from_content(content) -> str:
        """Extract plain text from message content (string or content blocks)."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    parts.append(block)
            return "\n".join(parts)
        return ""


def create_memory_files_if_needed(workspace_dir: Path, user_id: Optional[str] = None):
    """
    Create essential memory files if they don't exist.
    Only creates MEMORY.md; daily files are created lazily on first write.
    
    Args:
        workspace_dir: Workspace directory
        user_id: Optional user ID for user-specific files
    """
    memory_dir = workspace_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main MEMORY.md in workspace root (always needed for bootstrap)
    if user_id:
        user_dir = memory_dir / "users" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        main_memory = user_dir / "MEMORY.md"
    else:
        main_memory = Path(workspace_dir) / "MEMORY.md"
    
    if not main_memory.exists():
        main_memory.write_text("")


def ensure_daily_memory_file(workspace_dir: Path, user_id: Optional[str] = None) -> Path:
    """
    Ensure today's daily memory file exists, creating it only when actually needed.
    Called lazily before first write to daily memory.
    
    Args:
        workspace_dir: Workspace directory
        user_id: Optional user ID for user-specific files
        
    Returns:
        Path to today's memory file
    """
    memory_dir = workspace_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id:
        user_dir = memory_dir / "users" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        today_memory = user_dir / f"{today}.md"
    else:
        today_memory = memory_dir / f"{today}.md"
    
    if not today_memory.exists():
        today_memory.write_text(
            f"# Daily Memory: {today}\n\n"
        )
    
    return today_memory
