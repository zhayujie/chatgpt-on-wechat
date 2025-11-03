# tests/test_expired_dict.py
# Tests for common/expired_dict.py - time-based expiring dictionary

import time
import pytest
from common.expired_dict import ExpiredDict


class TestExpiredDict:
    """Test ExpiredDict time-based expiration functionality."""

    def test_set_and_get_before_expiry(self):
        """Test that values can be retrieved before expiration."""
        ed = ExpiredDict(expires_in_seconds=2)
        ed["key1"] = "value1"
        assert ed["key1"] == "value1"

    def test_get_after_expiry_raises_keyerror(self):
        """Test that expired keys raise KeyError."""
        ed = ExpiredDict(expires_in_seconds=1)
        ed["key1"] = "value1"
        time.sleep(1.1)  # Wait for expiration
        
        with pytest.raises(KeyError, match="expired key1"):
            _ = ed["key1"]

    def test_get_method_returns_default_for_expired(self):
        """Test that get() returns default for expired keys."""
        ed = ExpiredDict(expires_in_seconds=1)
        ed["key1"] = "value1"
        time.sleep(1.1)
        
        result = ed.get("key1", "default")
        assert result == "default"

    def test_contains_returns_false_for_expired(self):
        """Test that 'in' operator returns False for expired keys."""
        ed = ExpiredDict(expires_in_seconds=1)
        ed["key1"] = "value1"
        assert "key1" in ed
        
        time.sleep(1.1)
        assert "key1" not in ed

    def test_keys_excludes_expired(self):
        """Test that keys() only returns non-expired keys."""
        ed = ExpiredDict(expires_in_seconds=2)
        ed["key1"] = "value1"
        ed["key2"] = "value2"
        
        time.sleep(1)
        ed["key3"] = "value3"  # Fresh key
        time.sleep(1.1)  # key1 and key2 expired
        
        keys = list(ed.keys())
        assert "key3" in keys
        assert "key1" not in keys
        assert "key2" not in keys

    def test_items_excludes_expired(self):
        """Test that items() only returns non-expired items."""
        ed = ExpiredDict(expires_in_seconds=1)
        ed["key1"] = "value1"
        time.sleep(1.1)
        ed["key2"] = "value2"
        
        items = list(ed.items())
        assert ("key2", "value2") in items
        assert len(items) == 1

    def test_setitem_refreshes_expiry(self):
        """Test that setting an existing key refreshes its expiry time."""
        ed = ExpiredDict(expires_in_seconds=2)
        ed["key1"] = "value1"
        time.sleep(1)
        ed["key1"] = "value1_updated"  # Refresh expiry
        time.sleep(1.5)  # Original would have expired, but refresh extends it
        
        assert ed["key1"] == "value1_updated"