# tests/test_context.py
# Tests for bridge/context.py - Context class

import pytest
from bridge.context import Context, ContextType


class TestContextType:
    """Test ContextType enum."""

    def test_context_type_values(self):
        """Test that ContextType enum has expected values."""
        assert ContextType.TEXT.value == 1
        assert ContextType.VOICE.value == 2
        assert ContextType.IMAGE.value == 3

    def test_context_type_str(self):
        """Test string representation of ContextType."""
        assert str(ContextType.TEXT) == "TEXT"


class TestContext:
    """Test Context class dict-like interface."""

    def test_context_initialization(self):
        """Test creating a Context object."""
        ctx = Context(ContextType.TEXT, "Hello", {"key": "value"})
        assert ctx.type == ContextType.TEXT
        assert ctx.content == "Hello"
        assert ctx.kwargs == {"key": "value"}

    def test_context_getitem(self):
        """Test accessing Context items like a dict."""
        ctx = Context(ContextType.TEXT, "Hello", {"session_id": "123"})
        assert ctx["type"] == ContextType.TEXT
        assert ctx["content"] == "Hello"
        assert ctx["session_id"] == "123"

    def test_context_setitem(self):
        """Test setting Context items."""
        ctx = Context()
        ctx["type"] = ContextType.VOICE
        ctx["content"] = "audio.mp3"
        ctx["custom_key"] = "custom_value"
        
        assert ctx.type == ContextType.VOICE
        assert ctx.content == "audio.mp3"
        assert ctx.kwargs["custom_key"] == "custom_value"

    def test_context_contains(self):
        """Test 'in' operator for Context."""
        ctx = Context(ContextType.TEXT, "Hello", {"key": "value"})
        assert "type" in ctx
        assert "content" in ctx
        assert "key" in ctx
        assert "nonexistent" not in ctx

    def test_context_get_with_default(self):
        """Test get() method with default value."""
        ctx = Context(ContextType.TEXT, "Hello")
        assert ctx.get("type") == ContextType.TEXT
        assert ctx.get("nonexistent", "default") == "default"

    def test_context_delitem(self):
        """Test deleting Context items."""
        ctx = Context(ContextType.TEXT, "Hello", {"key": "value"})
        del ctx["key"]
        assert "key" not in ctx
        
        del ctx["type"]
        assert ctx.type is None

    def test_context_str(self):
        """Test string representation of Context."""
        ctx = Context(ContextType.TEXT, "Hello", {"key": "value"})
        result = str(ctx)
        assert "type=TEXT" in result
        assert "Hello" in result
        assert "'key': 'value'" in result