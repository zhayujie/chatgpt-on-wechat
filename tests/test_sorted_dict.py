# tests/test_sorted_dict.py
# Tests for common/sorted_dict.py - heap-based sorted dictionary

import pytest
from common.sorted_dict import SortedDict


class TestSortedDict:
    """Test SortedDict with custom sorting."""

    def test_sorted_by_key_ascending(self):
        """Test sorting by key in ascending order."""
        sd = SortedDict(sort_func=lambda k, v: k, reverse=False)
        sd[3] = "three"
        sd[1] = "one"
        sd[2] = "two"
        
        assert list(sd.keys()) == [1, 2, 3]

    def test_sorted_by_key_descending(self):
        """Test sorting by key in descending order."""
        sd = SortedDict(sort_func=lambda k, v: k, reverse=True)
        sd[3] = "three"
        sd[1] = "one"
        sd[2] = "two"
        
        assert list(sd.keys()) == [3, 2, 1]

    def test_sorted_by_value(self):
        """Test sorting by value."""
        sd = SortedDict(sort_func=lambda k, v: v, reverse=False)
        sd["a"] = 30
        sd["b"] = 10
        sd["c"] = 20
        
        assert list(sd.keys()) == ["b", "c", "a"]

    def test_update_value_resorts(self):
        """Test that updating a value triggers re-sorting."""
        sd = SortedDict(sort_func=lambda k, v: v, reverse=False)
        sd["a"] = 10
        sd["b"] = 20
        sd["c"] = 30
        
        assert list(sd.keys()) == ["a", "b", "c"]
        
        sd["a"] = 40  # Update to highest value
        assert list(sd.keys()) == ["b", "c", "a"]

    def test_delete_item(self):
        """Test deleting items from sorted dict."""
        sd = SortedDict(sort_func=lambda k, v: k)
        sd[1] = "one"
        sd[2] = "two"
        sd[3] = "three"
        
        del sd[2]
        assert list(sd.keys()) == [1, 3]

    def test_items_returns_sorted_tuples(self):
        """Test that items() returns sorted key-value pairs."""
        sd = SortedDict(sort_func=lambda k, v: k, reverse=False)
        sd[3] = "three"
        sd[1] = "one"
        sd[2] = "two"
        
        items = list(sd.items())
        assert items == [(1, "one"), (2, "two"), (3, "three")]

    def test_init_with_dict(self):
        """Test initialization with existing dictionary."""
        init_dict = {"a": 1, "b": 2, "c": 3}
        sd = SortedDict(sort_func=lambda k, v: v, init_dict=init_dict)
        
        assert list(sd.keys()) == ["a", "b", "c"]