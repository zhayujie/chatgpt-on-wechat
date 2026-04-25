"""
Memory search tool

Allows agents to search their memory using semantic and keyword search
"""

from typing import Dict, Any, Optional
from agent.tools.base_tool import BaseTool


class MemorySearchTool(BaseTool):
    """Tool for searching agent memory"""
    
    name: str = "memory_search"
    description: str = (
        "Search agent's long-term memory using semantic and keyword search. "
        "Use this to recall past conversations, preferences, and knowledge."
    )
    params: dict = {
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
                "description": "Minimum relevance score (0-1, default: 0.1)",
                "default": 0.1
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, memory_manager, user_id: Optional[str] = None):
        """
        Initialize memory search tool
        
        Args:
            memory_manager: MemoryManager instance
            user_id: Optional user ID for scoped search
        """
        super().__init__()
        self.memory_manager = memory_manager
        self.user_id = user_id

        from config import conf
        if conf().get("knowledge", True):
            self.description = (
                "Search agent's long-term memory and knowledge base using semantic and keyword search. "
                "Use this to recall past conversations, preferences, and knowledge pages."
            )
    
    def execute(self, args: dict):
        """
        Execute memory search
        
        Args:
            args: Dictionary with query, max_results, min_score
            
        Returns:
            ToolResult with formatted search results
        """
        from agent.tools.base_tool import ToolResult
        import asyncio
        
        query = args.get("query")
        max_results = args.get("max_results", 10)
        min_score = args.get("min_score", 0.1)
        
        if not query:
            return ToolResult.fail("Error: query parameter is required")
        
        try:
            # Run async search in sync context
            results = asyncio.run(self.memory_manager.search(
                query=query,
                user_id=self.user_id,
                max_results=max_results,
                min_score=min_score,
                include_shared=True
            ))
            
            if not results:
                # Return clear message that no memories exist yet
                # This prevents infinite retry loops
                return ToolResult.success(
                    f"No memories found for '{query}'. "
                    f"This is normal if no memories have been stored yet. "
                    f"You can store new memories by writing to MEMORY.md or memory/YYYY-MM-DD.md files."
                )
            
            output = [
                "[RAG_RESULTS]",
                f"Query: {query}",
                f"Hits: {len(results)}",
                f"Distinct Sources: {len({result.path for result in results})}",
                "",
            ]

            distinct_paths = []
            for result in results:
                if result.path not in distinct_paths:
                    distinct_paths.append(result.path)

            if len(distinct_paths) > 1:
                output.append(
                    "Next step: read at least the top 2 distinct relevant files with memory_get before answering."
                )
                output.append("")

            for i, result in enumerate(results, 1):
                metadata = result.metadata or {}
                source_type = metadata.get("source_type", result.source)
                title = metadata.get("title") or "Untitled"
                section_title = metadata.get("section_title") or ""
                category = metadata.get("category") or ""
                citation = metadata.get("citation") or self.memory_manager.build_citation(
                    result.path,
                    result.start_line,
                    result.end_line,
                    metadata,
                )

                output.append(
                    f"[{i}] score={result.score:.3f} source={result.path} "
                    f"lines={result.start_line}-{result.end_line} type={source_type}"
                )
                output.append(f"citation: {citation}")
                output.append(f"title: {title}")
                if section_title:
                    output.append(f"section: {section_title}")
                if category:
                    output.append(f"category: {category}")
                output.append("content:")
                output.append(result.snippet)
                output.append("")
            
            return ToolResult.success("\n".join(output))
            
        except Exception as e:
            return ToolResult.fail(f"Error searching memory: {str(e)}")
