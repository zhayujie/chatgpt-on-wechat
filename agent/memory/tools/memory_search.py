"""
Memory search tool

Allows agents to search their memory using semantic and keyword search
"""

from typing import Dict, Any, Optional
from agent.tools.base_tool import BaseTool
from agent.memory.manager import MemoryManager


class MemorySearchTool(BaseTool):
    """Tool for searching agent memory"""
    
    def __init__(self, memory_manager: MemoryManager, user_id: Optional[str] = None):
        """
        Initialize memory search tool
        
        Args:
            memory_manager: MemoryManager instance
            user_id: Optional user ID for scoped search
        """
        super().__init__()
        self.memory_manager = memory_manager
        self.user_id = user_id
        self._name = "memory_search"
        self._description = (
            "Search historical memory files (beyond today/yesterday) using semantic and keyword search. "
            "Recent context (MEMORY.md + today + yesterday) is already loaded. "
            "Use this ONLY for older dates, specific past events, or when current context lacks needed info."
        )
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (can be natural language question or keywords)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10)",
                    "default": 10
                },
                "min_score": {
                    "type": "number",
                    "description": "Minimum relevance score (0-1, default: 0.3)",
                    "default": 0.3
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, **kwargs) -> str:
        """
        Execute memory search
        
        Args:
            query: Search query
            max_results: Maximum results
            min_score: Minimum score
            
        Returns:
            Formatted search results
        """
        query = kwargs.get("query")
        max_results = kwargs.get("max_results", 10)
        min_score = kwargs.get("min_score", 0.3)
        
        if not query:
            return "Error: query parameter is required"
        
        try:
            results = await self.memory_manager.search(
                query=query,
                user_id=self.user_id,
                max_results=max_results,
                min_score=min_score,
                include_shared=True
            )
            
            if not results:
                return f"No relevant memories found for query: {query}"
            
            # Format results
            output = [f"Found {len(results)} relevant memories:\n"]
            
            for i, result in enumerate(results, 1):
                output.append(f"\n{i}. {result.path} (lines {result.start_line}-{result.end_line})")
                output.append(f"   Score: {result.score:.3f}")
                output.append(f"   Snippet: {result.snippet}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error searching memory: {str(e)}"
