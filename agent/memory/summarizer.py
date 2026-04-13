"""
Memory flush manager (with Light Dream)

Handles memory persistence when conversation context is trimmed or overflows:
- Uses LLM to summarize discarded messages into concise key-information entries
- Writes to daily memory files (lazy creation)
- Light Dream: extracts long-term memories to MEMORY.md in the same LLM call
- Deduplicates trim flushes to avoid repeated writes
- Runs summarization asynchronously to avoid blocking normal replies
- Provides daily summary interface for scheduler
"""

import threading
from typing import Optional, Callable, Any, List, Dict
from pathlib import Path
from datetime import datetime
from common.log import logger


SUMMARIZE_SYSTEM_PROMPT = """你是一个记忆提取助手。你的任务是从对话记录中提炼出两种记忆：

## 第一部分：日常记录（[DAILY]）

按「事件」维度归纳当天发生的事，不要按对话轮次逐条记录：
- 每条一行，用 "- " 开头
- 合并同一件事的多轮对话
- 只记录有意义的事件，忽略闲聊和问候

## 第二部分：长期记忆（[MEMORY]）

提取值得**永久记住**的关键信息，这些信息在未来的对话中仍然有价值：
- 用户的偏好、习惯、风格
- 重要的决策或约定
- 关键人物关系
- 用户明确要求记住的内容
- 重要的教训或经验总结

**如果没有值得永久记住的信息，[MEMORY] 部分留空即可。**

## 输出格式（严格遵守）

```
[DAILY]
- 事件1的摘要
- 事件2的摘要

[MEMORY]
- 值得永久记住的信息1
- 值得永久记住的信息2
```

当对话没有任何记录价值（仅含问候或无意义内容），直接回复"无"。"""

SUMMARIZE_USER_PROMPT = """请从以下对话记录中提取记忆（按 [DAILY] 和 [MEMORY] 两部分输出）：

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
        context_summary_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        Asynchronously summarize and flush messages to daily memory.

        Deduplication runs synchronously, then LLM summarization + file write
        run in a background thread so the main reply flow is never blocked.

        If *context_summary_callback* is provided, it is called with the
        [DAILY] portion of the LLM summary once available. The caller can use
        this to inject the summary into the live message list for context
        continuity — one LLM call serves both disk persistence and in-context
        injection.
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
                args=(snapshot, user_id, reason, max_messages, context_summary_callback),
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
        context_summary_callback: Optional[Callable[[str], None]] = None,
    ):
        """Background worker: summarize with LLM, write daily file + MEMORY.md (Light Dream)."""
        try:
            raw_summary = self._summarize_messages(messages, max_messages)
            if not raw_summary or not raw_summary.strip() or raw_summary.strip() == "无":
                logger.info(f"[MemoryFlush] No valuable content to flush (reason={reason})")
                return

            daily_part, memory_part = self._parse_dual_output(raw_summary)

            # --- Write daily memory ---
            if daily_part:
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

                flush_entry = f"\n{header}\n\n{note}{daily_part}\n"

                with open(daily_file, "a", encoding="utf-8") as f:
                    f.write(flush_entry)

                logger.info(f"[MemoryFlush] Wrote daily memory to {daily_file.name} (reason={reason}, chars={len(daily_part)})")

            # --- Light Dream: write long-term memory to MEMORY.md ---
            if memory_part:
                self._append_to_main_memory(memory_part, user_id)

            # --- Inject context summary into live messages (if callback provided) ---
            if context_summary_callback and daily_part:
                try:
                    context_summary_callback(daily_part)
                except Exception as e:
                    logger.warning(f"[MemoryFlush] Context summary callback failed: {e}")

            self.last_flush_timestamp = datetime.now()

        except Exception as e:
            logger.warning(f"[MemoryFlush] Async flush failed (reason={reason}): {e}")

    @staticmethod
    def _parse_dual_output(raw: str) -> tuple:
        """
        Parse LLM output into (daily_part, memory_part).
        Handles both new [DAILY]/[MEMORY] format and legacy single-section format.
        """
        raw = raw.strip()

        if "[DAILY]" in raw or "[MEMORY]" in raw:
            daily_part = ""
            memory_part = ""

            # Extract [DAILY] section
            if "[DAILY]" in raw:
                start = raw.index("[DAILY]") + len("[DAILY]")
                end = raw.index("[MEMORY]") if "[MEMORY]" in raw else len(raw)
                daily_part = raw[start:end].strip()

            # Extract [MEMORY] section
            if "[MEMORY]" in raw:
                start = raw.index("[MEMORY]") + len("[MEMORY]")
                memory_part = raw[start:].strip()

            # Filter out empty markers
            if memory_part and all(
                not line.strip() or line.strip() == "-"
                for line in memory_part.split("\n")
            ):
                memory_part = ""

            return daily_part, memory_part

        # Legacy format: treat entire output as daily, no memory extraction
        return raw, ""

    def _append_to_main_memory(self, memory_entries: str, user_id: Optional[str] = None):
        """Append extracted long-term memories to MEMORY.md with date stamp."""
        try:
            main_file = self.get_main_memory_file(user_id)
            today = datetime.now().strftime("%Y-%m-%d")

            # Add date prefix to each entry line
            stamped_lines = []
            for line in memory_entries.strip().split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    stamped_lines.append(f"- ({today}) {line[2:]}")
                elif line:
                    stamped_lines.append(f"- ({today}) {line}")

            if not stamped_lines:
                return

            stamped_text = "\n".join(stamped_lines)

            with open(main_file, "a", encoding="utf-8") as f:
                f.write(f"\n{stamped_text}\n")

            logger.info(f"[LightDream] Appended {len(stamped_lines)} entries to MEMORY.md")

        except Exception as e:
            logger.warning(f"[LightDream] Failed to append to MEMORY.md: {e}")

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
        
        if self.llm_model:
            try:
                summary = self._call_llm_for_summary(conversation_text)
                if summary and summary.strip() and summary.strip() != "无":
                    return summary.strip()
                logger.info(f"[MemoryFlush] LLM returned empty or '无', using fallback")
            except Exception as e:
                logger.warning(f"[MemoryFlush] LLM summarization failed, using fallback: {e}")
        else:
            logger.info("[MemoryFlush] No LLM model available, using rule-based fallback")
        
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

    @staticmethod
    def _extract_response_text(response) -> str:
        """
        Extract text from LLM response regardless of format.

        Handles:
        - Generator (MiniMax _handle_sync_response yields Claude-format dicts)
        - Claude format: {"role":"assistant","content":[{"type":"text","text":"..."}]}
        - OpenAI format: {"choices":[{"message":{"content":"..."}}]}
        - OpenAI SDK response object with .choices attribute
        """
        import types

        # Unwrap generator — consume first yielded item
        if isinstance(response, types.GeneratorType):
            try:
                response = next(response)
            except StopIteration:
                return ""

        if not response:
            return ""

        if isinstance(response, dict):
            # Check for error
            if response.get("error"):
                raise RuntimeError(response.get("message", "LLM call failed"))

            # Claude format: content is a list of blocks
            content = response.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", "")

            # OpenAI format
            choices = response.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")

        # OpenAI SDK response object
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content or ""

        return ""

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
        return self._extract_response_text(response)

    @staticmethod
    def _extract_first_meaningful_line(text: str, max_len: int = 120) -> str:
        """Extract the first meaningful line from assistant reply, skipping markdown noise."""
        import re
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Skip markdown headings, horizontal rules, code fences, pure emoji/symbols
            if re.match(r'^(#{1,4}\s|```|---|\*\*\*|[-*]\s*$|[^\w\u4e00-\u9fff]{1,5}$)', line):
                continue
            # Strip leading markdown bold/emoji decorations
            cleaned = re.sub(r'^[\*#>\-\s]+', '', line).strip()
            cleaned = re.sub(r'^[\U0001f300-\U0001f9ff\u2600-\u27bf\s]+', '', cleaned).strip()
            if len(cleaned) >= 5:
                return cleaned[:max_len]
        return text.split("\n")[0].strip()[:max_len]

    @staticmethod
    def _extract_summary_fallback(messages: List[Dict], max_messages: int = 0) -> str:
        """
        Rule-based summary of discarded messages.
        Format: "用户问了X; 助手回答了Y" per event, compact and readable.
        """
        msgs = messages if max_messages == 0 else messages[-max_messages * 2:]

        events: List[str] = []
        current_user_text = ""
        for msg in msgs:
            role = msg.get("role", "")
            text = MemoryFlushManager._extract_text_from_content(msg.get("content", ""))
            if not text or not text.strip():
                continue
            text = text.strip()

            if role == "user":
                if len(text) <= 3:
                    continue
                current_user_text = text[:120]
            elif role == "assistant" and current_user_text:
                reply_summary = MemoryFlushManager._extract_first_meaningful_line(text)
                if reply_summary:
                    events.append(f"- 用户: {current_user_text} → 回复: {reply_summary}")
                else:
                    events.append(f"- 用户: {current_user_text}")
                current_user_text = ""

        if current_user_text:
            events.append(f"- 用户: {current_user_text}")

        return "\n".join(events[:10])
    
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
