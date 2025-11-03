# tests/test_config.py
# Tests for config.py - configuration management

import json
import os
import pytest
from unittest.mock import patch, mock_open
from config import Config, drag_sensitive, load_config


class TestConfig:
    """Test Config class."""

    def test_config_initialization(self):
        """Test creating Config with initial values."""
        config = Config({"model": "gpt-4", "debug": True})
        assert config.get("model") == "gpt-4"
        assert config.get("debug") is True

    def test_config_getitem_valid_key(self):
        """Test accessing valid config keys."""
        config = Config({"model": "gpt-3.5-turbo"})
        assert config["model"] == "gpt-3.5-turbo"

    def test_config_getitem_invalid_key(self):
        """Test that invalid keys raise exception."""
        config = Config()
        with pytest.raises(Exception, match="not in available_setting"):
            _ = config["invalid_key"]

    def test_config_setitem_valid_key(self):
        """Test setting valid config keys."""
        config = Config()
        config["model"] = "gpt-4"
        assert config["model"] == "gpt-4"

    def test_config_setitem_invalid_key(self):
        """Test that setting invalid keys raises exception."""
        config = Config()
        with pytest.raises(Exception, match="not in available_setting"):
            config["invalid_key"] = "value"

    def test_config_get_with_default(self):
        """Test get() method behavior when key exists and when it doesn't."""
        config = Config({"model": "gpt-3.5-turbo"})
        
        # should return correct value for existing key
        assert config.get("model") == "gpt-3.5-turbo"

        # should raise an error for nonexistent key
        with pytest.raises(Exception):
            config.get("nonexistent", "default")

    def test_get_user_data_creates_new(self):
        """Test that get_user_data creates new dict for new users."""
        config = Config()
        user_data = config.get_user_data("user123")
        assert isinstance(user_data, dict)
        assert user_data == {}

    def test_get_user_data_returns_existing(self):
        """Test that get_user_data returns existing user data."""
        config = Config()
        config.user_datas["user123"] = {"key": "value"}
        user_data = config.get_user_data("user123")
        assert user_data == {"key": "value"}


class TestDragSensitive:
    """Test sensitive data masking."""

    def test_drag_sensitive_string_with_key(self):
        """Test masking keys in JSON string."""
        config_str = '{"api_key": "sk-1234567890abcdef", "model": "gpt-4"}'
        result = drag_sensitive(config_str)
        result_dict = json.loads(result)
        
        # API key should be masked
        assert result_dict["api_key"].startswith("sk-")
        assert "*****" in result_dict["api_key"]
        assert result_dict["api_key"].endswith("def")
        
        # Model should not be masked
        assert result_dict["model"] == "gpt-4"

    def test_drag_sensitive_dict_with_secret(self):
        """Test masking secrets in dictionary."""
        config_dict = {
            "secret_key": "secret123456789",
            "normal_field": "value"
        }
        result = drag_sensitive(config_dict)
        
        assert "*****" in result["secret_key"]
        assert result["normal_field"] == "value"

    def test_drag_sensitive_short_key(self):
        """Test masking very short keys."""
        config_dict = {"api_key": "abc"}
        result = drag_sensitive(config_dict)
        # Should handle short keys gracefully
        assert "api_key" in result