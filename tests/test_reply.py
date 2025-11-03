# tests/test_reply.py
# Tests for bridge/reply.py - Reply class

import pytest
from bridge.reply import Reply, ReplyType


class TestReplyType:
    """Test ReplyType enum."""

    def test_reply_type_values(self):
        """Test that ReplyType enum has expected values."""
        assert ReplyType.TEXT.value == 1
        assert ReplyType.VOICE.value == 2
        assert ReplyType.IMAGE.value == 3

    def test_reply_type_str(self):
        """Test string representation of ReplyType."""
        assert str(ReplyType.TEXT) == "TEXT"


class TestReply:
    """Test Reply class."""

    def test_reply_initialization(self):
        """Test creating a Reply object."""
        reply = Reply(ReplyType.TEXT, "Hello World")
        assert reply.type == ReplyType.TEXT
        assert reply.content == "Hello World"

    def test_reply_default_initialization(self):
        """Test creating Reply with no arguments."""
        reply = Reply()
        assert reply.type is None
        assert reply.content is None

    def test_reply_str(self):
        """Test string representation of Reply."""
        reply = Reply(ReplyType.ERROR, "Error message")
        result = str(reply)
        assert "type=ERROR" in result
        assert "Error message" in result