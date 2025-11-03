# tests/test_singleton.py
# Tests for common/singleton.py - singleton decorator

import pytest
from common.singleton import singleton


class TestSingleton:
    """Test singleton decorator."""

    def test_singleton_returns_same_instance(self):
        """Test that singleton decorator returns same instance."""
        @singleton
        class TestClass:
            def __init__(self, value):
                self.value = value
        
        instance1 = TestClass(10)
        instance2 = TestClass(20)  # Should return same instance
        
        assert instance1 is instance2
        assert instance1.value == 10  # Value from first instantiation

    def test_singleton_different_classes(self):
        """Test that different classes get different instances."""
        @singleton
        class ClassA:
            pass
        
        @singleton
        class ClassB:
            pass
        
        instance_a = ClassA()
        instance_b = ClassB()
        
        assert instance_a is not instance_b