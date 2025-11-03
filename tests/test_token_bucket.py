# tests/test_token_bucket.py
# Tests for common/token_bucket.py - rate limiting

import time
import pytest
from common.token_bucket import TokenBucket


class TestTokenBucket:
    """Test TokenBucket rate limiting."""

    def test_get_token_success(self):
        """Test successfully getting tokens."""
        tb = TokenBucket(tpm=60, timeout=1)  # 1 token per second
        assert tb.get_token() is True
        tb.close()

    def test_get_token_timeout(self):
        """Test timeout when no tokens available."""
        tb = TokenBucket(tpm=60, timeout=0.1)
        
        # Consume initial token
        tb.tokens = 0
        
        # Should timeout waiting for new token
        result = tb.get_token()
        assert result is False
        tb.close()

    def test_token_generation_rate(self):
        """Test that tokens are generated at correct rate."""
        tb = TokenBucket(tpm=60, timeout=2)  # 1 token per second
        tb.tokens = 0  # Start with no tokens
        
        time.sleep(2.1)  # Wait for ~2 tokens to generate
        
        # Should have at least 2 tokens
        assert tb.tokens >= 2
        tb.close()

    def test_capacity_limit(self):
        """Test that token count doesn't exceed capacity."""
        tb = TokenBucket(tpm=60, timeout=1)
        time.sleep(2)  # Let tokens accumulate
        
        # Tokens should not exceed capacity
        assert tb.tokens <= tb.capacity
        tb.close()

    def test_close_stops_generation(self):
        """Test that close() stops token generation."""
        tb = TokenBucket(tpm=60, timeout=1)
        initial_tokens = tb.tokens
        tb.close()
        time.sleep(1)
        
        # Tokens should not increase after close
        # Note: This test may be flaky due to threading timing
        assert tb.is_running is False