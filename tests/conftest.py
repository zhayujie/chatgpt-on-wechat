# tests/conftest.py
# Pytest configuration and shared fixtures

import os
import sys
import tempfile
import pytest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_config():
    """Mock the global config object."""
    from config import Config
    mock_conf = Config({
        "expires_in_seconds": 3600,
        "character_desc": "Test bot",
        "conversation_max_tokens": 1000,
        "debug": False,
    })
    return mock_conf


@pytest.fixture
def mock_logger():
    """Mock logger to avoid log output during tests."""
    return MagicMock()