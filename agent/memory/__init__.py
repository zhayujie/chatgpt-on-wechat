"""
Memory module for AgentMesh

Provides long-term memory capabilities with hybrid search (vector + keyword)
"""

from agent.memory.manager import MemoryManager
from agent.memory.config import MemoryConfig, get_default_memory_config, set_global_memory_config
from agent.memory.embedding import create_embedding_provider

__all__ = ['MemoryManager', 'MemoryConfig', 'get_default_memory_config', 'set_global_memory_config', 'create_embedding_provider']
