"""
Message sanitizer — fix broken tool_use / tool_result pairs.

Provides two public helpers that can be reused across agent_stream.py
and any bot that converts messages to OpenAI format:

1. sanitize_claude_messages(messages)
   Operates on the internal Claude-format message list (in-place).

2. drop_orphaned_tool_results_openai(messages)
   Operates on an already-converted OpenAI-format message list,
   returning a cleaned copy.
"""

from __future__ import annotations

from typing import Dict, List, Set

from common.log import logger


# ------------------------------------------------------------------ #
# Claude-format sanitizer (used by agent_stream)
# ------------------------------------------------------------------ #

def sanitize_claude_messages(messages: List[Dict]) -> int:
    """
    Validate and fix a Claude-format message list **in-place**.

    Fixes handled:
    - Trailing assistant message with tool_use but no following tool_result
    - Leading orphaned tool_result user messages
    - Mid-list tool_result blocks whose tool_use_id has no matching
      tool_use in any preceding assistant message

    Returns the number of messages / blocks removed.
    """
    if not messages:
        return 0

    removed = 0

    # 1. Remove trailing incomplete tool_use assistant messages
    while messages:
        last = messages[-1]
        if last.get("role") != "assistant":
            break
        content = last.get("content", [])
        if isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_use"
            for b in content
        ):
            logger.warning("⚠️ Removing trailing incomplete tool_use assistant message")
            messages.pop()
            removed += 1
        else:
            break

    # 2. Remove leading orphaned tool_result user messages
    while messages:
        first = messages[0]
        if first.get("role") != "user":
            break
        content = first.get("content", [])
        if isinstance(content, list) and _has_block_type(content, "tool_result") \
                and not _has_block_type(content, "text"):
            logger.warning("⚠️ Removing leading orphaned tool_result user message")
            messages.pop(0)
            removed += 1
        else:
            break

    # 3. Full scan: ensure every tool_result references a known tool_use id
    known_ids: Set[str] = set()
    i = 0
    while i < len(messages):
        msg = messages[i]
        role = msg.get("role")
        content = msg.get("content", [])

        if role == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tid = block.get("id", "")
                    if tid:
                        known_ids.add(tid)

        elif role == "user" and isinstance(content, list):
            if not _has_block_type(content, "tool_result"):
                i += 1
                continue

            orphaned = [
                b.get("tool_use_id", "")
                for b in content
                if isinstance(b, dict)
                and b.get("type") == "tool_result"
                and b.get("tool_use_id", "")
                and b.get("tool_use_id", "") not in known_ids
            ]
            if orphaned:
                orphaned_set = set(orphaned)
                if not _has_block_type(content, "text"):
                    logger.warning(
                        f"⚠️ Removing orphaned tool_result message (tool_ids: {orphaned})"
                    )
                    messages.pop(i)
                    removed += 1
                    # Also remove a preceding broken assistant tool_use message
                    if i > 0 and messages[i - 1].get("role") == "assistant":
                        prev = messages[i - 1].get("content", [])
                        if isinstance(prev, list) and _has_block_type(prev, "tool_use"):
                            messages.pop(i - 1)
                            removed += 1
                            i -= 1
                    continue
                else:
                    new_content = [
                        b for b in content
                        if not (
                            isinstance(b, dict)
                            and b.get("type") == "tool_result"
                            and b.get("tool_use_id", "") in orphaned_set
                        )
                    ]
                    delta = len(content) - len(new_content)
                    if delta:
                        logger.warning(
                            f"⚠️ Stripped {delta} orphaned tool_result block(s) from mixed message"
                        )
                        msg["content"] = new_content
                        removed += delta
        i += 1

    if removed:
        logger.info(f"🔧 Message validation: removed {removed} broken message(s)")
    return removed


# ------------------------------------------------------------------ #
# OpenAI-format sanitizer (used by minimax_bot, openai_compatible_bot)
# ------------------------------------------------------------------ #

def drop_orphaned_tool_results_openai(messages: List[Dict]) -> List[Dict]:
    """
    Return a copy of *messages* (OpenAI format) with any ``role=tool``
    messages removed if their ``tool_call_id`` does not match a
    ``tool_calls[].id`` in a preceding assistant message.
    """
    known_ids: Set[str] = set()
    cleaned: List[Dict] = []
    for msg in messages:
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tc_id = tc.get("id", "")
                if tc_id:
                    known_ids.add(tc_id)

        if msg.get("role") == "tool":
            ref_id = msg.get("tool_call_id", "")
            if ref_id and ref_id not in known_ids:
                logger.warning(
                    f"[MessageSanitizer] Dropping orphaned tool result "
                    f"(tool_call_id={ref_id} not in known ids)"
                )
                continue
        cleaned.append(msg)
    return cleaned


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #

def _has_block_type(content: list, block_type: str) -> bool:
    return any(
        isinstance(b, dict) and b.get("type") == block_type
        for b in content
    )
