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

    # 3. Iteratively remove unmatched tool_use / tool_result until stable.
    #    Removing one broken message can orphan others (e.g. an assistant msg
    #    with both matched and unmatched tool_use — deleting it orphans the
    #    previously-matched tool_result).  Loop until clean.
    for _ in range(5):
        use_ids: Set[str] = set()
        result_ids: Set[str] = set()
        for msg in messages:
            for block in (msg.get("content") or []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and block.get("id"):
                    use_ids.add(block["id"])
                elif block.get("type") == "tool_result" and block.get("tool_use_id"):
                    result_ids.add(block["tool_use_id"])

        bad_use = use_ids - result_ids
        bad_result = result_ids - use_ids
        if not bad_use and not bad_result:
            break

        pass_removed = 0
        i = 0
        while i < len(messages):
            msg = messages[i]
            role = msg.get("role")
            content = msg.get("content", [])
            if not isinstance(content, list):
                i += 1
                continue

            if role == "assistant" and bad_use and any(
                isinstance(b, dict) and b.get("type") == "tool_use"
                and b.get("id") in bad_use for b in content
            ):
                logger.warning(f"⚠️ Removing assistant msg with unmatched tool_use")
                messages.pop(i)
                pass_removed += 1
                continue

            if role == "user" and bad_result and _has_block_type(content, "tool_result"):
                has_bad = any(
                    isinstance(b, dict) and b.get("type") == "tool_result"
                    and b.get("tool_use_id") in bad_result for b in content
                )
                if has_bad:
                    if not _has_block_type(content, "text"):
                        logger.warning(f"⚠️ Removing user msg with unmatched tool_result")
                        messages.pop(i)
                        pass_removed += 1
                        continue
                    else:
                        before = len(content)
                        msg["content"] = [
                            b for b in content
                            if not (isinstance(b, dict) and b.get("type") == "tool_result"
                                    and b.get("tool_use_id") in bad_result)
                        ]
                        pass_removed += before - len(msg["content"])

            i += 1

        removed += pass_removed
        if pass_removed == 0:
            break

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


def _extract_text_from_content(content) -> str:
    """Extract plain text from a message content field (str or list of blocks)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        return "\n".join(p for p in parts if p).strip()
    return ""


def compress_turn_to_text_only(turn: Dict) -> Dict:
    """
    Compress a full turn (with tool_use/tool_result chains) into a lightweight
    text-only turn that keeps only the first user text and the last assistant text.

    This preserves the conversational context (what the user asked and what the
    agent concluded) while stripping out the bulky intermediate tool interactions.

    Returns a new turn dict with a ``messages`` list; the original is not mutated.
    """
    user_text = ""
    last_assistant_text = ""

    for msg in turn["messages"]:
        role = msg.get("role")
        content = msg.get("content", [])

        if role == "user":
            if isinstance(content, list) and _has_block_type(content, "tool_result"):
                continue
            if not user_text:
                user_text = _extract_text_from_content(content)

        elif role == "assistant":
            text = _extract_text_from_content(content)
            if text:
                last_assistant_text = text

    compressed_messages = []
    if user_text:
        compressed_messages.append({
            "role": "user",
            "content": [{"type": "text", "text": user_text}]
        })
    if last_assistant_text:
        compressed_messages.append({
            "role": "assistant",
            "content": [{"type": "text", "text": last_assistant_text}]
        })

    return {"messages": compressed_messages}
