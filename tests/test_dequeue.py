# tests/test_dequeue.py
# Tests for common/dequeue.py - custom queue with putleft

import pytest
from queue import Full
from common.dequeue import Dequeue


class TestDequeue:
    """Test Dequeue with putleft functionality."""

    def test_putleft_adds_to_front(self):
        """Test that putleft adds items to front of queue."""
        dq = Dequeue()
        dq.put("first")
        dq.putleft("second")
        
        # Second should come out first
        assert dq.get() == "second"
        assert dq.get() == "first"

    def test_putleft_nowait(self):
        """Test putleft_nowait method."""
        dq = Dequeue()
        dq.putleft_nowait("item")
        assert dq.get() == "item"

    def test_putleft_with_maxsize(self):
        """Test putleft respects maxsize."""
        dq = Dequeue(maxsize=2)
        dq.put("first")
        dq.put("second")
        
        # Queue is full, putleft with block=False should raise Full
        with pytest.raises(Full):
            dq.putleft("third", block=False)

    def test_mixed_put_and_putleft(self):
        """Test mixing put and putleft operations."""
        dq = Dequeue()
        dq.put("1")
        dq.putleft("2")
        dq.put("3")
        dq.putleft("4")
        
        # Order should be: 4, 2, 1, 3
        assert dq.get() == "4"
        assert dq.get() == "2"
        assert dq.get() == "1"
        assert dq.get() == "3"