# tests/test_session_manager.py
# Tests for bot/session_manager.py - session management

import pytest
from unittest.mock import MagicMock, patch
from bot.session_manager import Session, SessionManager


class MockSession(Session):
    """Mock Session for testing."""
    
    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        return 100  # Mock token count
    
    def calc_tokens(self):
        return 100


class TestSession:
    """Test Session class."""

    def test_session_initialization(self):
        """Test creating a Session."""
        with patch('bot.session_manager.conf') as mock_conf:
            mock_conf.return_value.get.return_value = "Default prompt"
            session = Session("session123")
            
            assert session.session_id == "session123"
            assert session.system_prompt == "Default prompt"
            assert session.messages == []

    def test_session_reset(self):
        """Test resetting a session."""
        session = Session("session123", "Test prompt")
        session.messages = [{"role": "user", "content": "test"}]
        
        session.reset()
        
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"
        assert session.messages[0]["content"] == "Test prompt"

    def test_add_query(self):
        """Test adding user query to session."""
        session = Session("session123", "Test prompt")
        session.add_query("Hello")
        
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "Hello"

    def test_add_reply(self):
        """Test adding assistant reply to session."""
        session = Session("session123", "Test prompt")
        session.add_reply("Hi there")
        
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "assistant"
        assert session.messages[0]["content"] == "Hi there"

    def test_set_system_prompt(self):
        """Test updating system prompt resets session."""
        session = Session("session123", "Old prompt")
        session.messages = [{"role": "user", "content": "test"}]
        
        session.set_system_prompt("New prompt")
        
        assert session.system_prompt == "New prompt"
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "system"


class TestSessionManager:
    """Test SessionManager class."""

    def test_build_session_creates_new(self):
        """Test that build_session creates new session if not exists."""
        with patch('bot.session_manager.conf') as mock_conf:
            mock_conf.return_value.get.return_value = 3600
            
            sm = SessionManager(MockSession)
            session = sm.build_session("session123")
            
            assert session.session_id == "session123"
            assert "session123" in sm.sessions

    def test_build_session_returns_existing(self):
        """Test that build_session returns existing session."""
        with patch('bot.session_manager.conf') as mock_conf:
            mock_conf.return_value.get.return_value = 3600
            
            sm = SessionManager(MockSession)
            session1 = sm.build_session("session123")
            session2 = sm.build_session("session123")
            
            assert session1 is session2

    def test_build_session_updates_system_prompt(self):
        """Test that build_session updates system prompt if provided."""
        with patch('bot.session_manager.conf') as mock_conf:
            mock_conf.return_value.get.return_value = 3600
            
            sm = SessionManager(MockSession)
            session1 = sm.build_session("session123", "Prompt 1")
            session2 = sm.build_session("session123", "Prompt 2")
            
            assert session2.system_prompt == "Prompt 2"

    def test_clear_session(self):
        """Test clearing a specific session."""
        with patch('bot.session_manager.conf') as mock_conf:
            mock_conf.return_value.get.return_value = 3600
            
            sm = SessionManager(MockSession)
            sm.build_session("session123")
            
            assert "session123" in sm.sessions
            sm.clear_session("session123")
            assert "session123" not in sm.sessions

    def test_clear_all_session(self):
        """Test clearing all sessions."""
        with patch('bot.session_manager.conf') as mock_conf:
            mock_conf.return_value.get.return_value = 3600
            
            sm = SessionManager(MockSession)
            sm.build_session("session1")
            sm.build_session("session2")
            
            sm.clear_all_session()
            assert len(sm.sessions) == 0