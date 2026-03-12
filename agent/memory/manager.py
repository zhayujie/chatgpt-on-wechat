"""
Memory manager for AgentMesh

Provides high-level interface for memory operations
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import hashlib
from datetime import datetime, timedelta

from agent.memory.config import MemoryConfig, get_default_memory_config
from agent.memory.storage import MemoryStorage, MemoryChunk, SearchResult
from agent.memory.chunker import TextChunker
from agent.memory.embedding import create_embedding_provider, EmbeddingProvider
from agent.memory.summarizer import MemoryFlushManager, create_memory_files_if_needed


class MemoryManager:
    """
    Memory manager with hybrid search capabilities
    
    Provides long-term memory for agents with vector and keyword search
    """
    
    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        llm_model: Optional[Any] = None
    ):
        """
        Initialize memory manager
        
        Args:
            config: Memory configuration (uses global config if not provided)
            embedding_provider: Custom embedding provider (optional)
            llm_model: LLM model for summarization (optional)
        """
        self.config = config or get_default_memory_config()
        
        # Initialize storage
        db_path = self.config.get_db_path()
        self.storage = MemoryStorage(db_path)
        
        # Initialize chunker
        self.chunker = TextChunker(
            max_tokens=self.config.chunk_max_tokens,
            overlap_tokens=self.config.chunk_overlap_tokens
        )
        
        # Initialize embedding provider (optional, prefer OpenAI, fallback to LinkAI)
        self.embedding_provider = None
        if embedding_provider:
            self.embedding_provider = embedding_provider
        else:
            # Try OpenAI first
            try:
                api_key = os.environ.get('OPENAI_API_KEY')
                api_base = os.environ.get('OPENAI_API_BASE')
                if api_key:
                    self.embedding_provider = create_embedding_provider(
                        provider="openai",
                        model=self.config.embedding_model,
                        api_key=api_key,
                        api_base=api_base
                    )
            except Exception as e:
                from common.log import logger
                logger.warning(f"[MemoryManager] OpenAI embedding failed: {e}")

            # Fallback to LinkAI
            if self.embedding_provider is None:
                try:
                    linkai_key = os.environ.get('LINKAI_API_KEY')
                    linkai_base = os.environ.get('LINKAI_API_BASE', 'https://api.link-ai.tech')
                    if linkai_key:
                        self.embedding_provider = create_embedding_provider(
                            provider="linkai",
                            model=self.config.embedding_model,
                            api_key=linkai_key,
                            api_base=f"{linkai_base}/v1"
                        )
                except Exception as e:
                    from common.log import logger
                    logger.warning(f"[MemoryManager] LinkAI embedding failed: {e}")

            if self.embedding_provider is None:
                from common.log import logger
                logger.info(f"[MemoryManager] Memory will work with keyword search only (no vector search)")
        
        # Initialize memory flush manager
        workspace_dir = self.config.get_workspace()
        self.flush_manager = MemoryFlushManager(
            workspace_dir=workspace_dir,
            llm_model=llm_model
        )
        
        # Ensure workspace directories exist
        self._init_workspace()
        
        self._dirty = False
    
    def _init_workspace(self):
        """Initialize workspace directories"""
        memory_dir = self.config.get_memory_dir()
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default memory files
        workspace_dir = self.config.get_workspace()
        create_memory_files_if_needed(workspace_dir)
    
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        max_results: Optional[int] = None,
        min_score: Optional[float] = None,
        include_shared: bool = True
    ) -> List[SearchResult]:
        """
        Search memory with hybrid search (vector + keyword)
        
        Args:
            query: Search query
            user_id: User ID for scoped search
            max_results: Maximum results to return
            min_score: Minimum score threshold
            include_shared: Include shared memories
            
        Returns:
            List of search results sorted by relevance
        """
        max_results = max_results or self.config.max_results
        min_score = min_score or self.config.min_score
        
        # Determine scopes
        scopes = []
        if include_shared:
            scopes.append("shared")
        if user_id:
            scopes.append("user")
        
        if not scopes:
            return []
        
        # Sync if needed
        if self.config.sync_on_search and self._dirty:
            await self.sync()
        
        # Perform vector search (if embedding provider available)
        vector_results = []
        if self.embedding_provider:
            try:
                from common.log import logger
                query_embedding = self.embedding_provider.embed(query)
                vector_results = self.storage.search_vector(
                    query_embedding=query_embedding,
                    user_id=user_id,
                    scopes=scopes,
                    limit=max_results * 2  # Get more candidates for merging
                )
                logger.info(f"[MemoryManager] Vector search found {len(vector_results)} results for query: {query}")
            except Exception as e:
                from common.log import logger
                logger.warning(f"[MemoryManager] Vector search failed: {e}")
        
        # Perform keyword search
        keyword_results = self.storage.search_keyword(
            query=query,
            user_id=user_id,
            scopes=scopes,
            limit=max_results * 2
        )
        from common.log import logger
        logger.info(f"[MemoryManager] Keyword search found {len(keyword_results)} results for query: {query}")
        
        # Merge results
        merged = self._merge_results(
            vector_results,
            keyword_results,
            self.config.vector_weight,
            self.config.keyword_weight
        )
        
        # Filter by min score and limit
        filtered = [r for r in merged if r.score >= min_score]
        return filtered[:max_results]
    
    async def add_memory(
        self,
        content: str,
        user_id: Optional[str] = None,
        scope: str = "shared",
        source: str = "memory",
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add new memory content
        
        Args:
            content: Memory content
            user_id: User ID for user-scoped memory
            scope: Memory scope ("shared", "user", "session")
            source: Memory source ("memory" or "session")
            path: File path (auto-generated if not provided)
            metadata: Additional metadata
        """
        if not content.strip():
            return
        
        # Generate path if not provided
        if not path:
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
            if user_id and scope == "user":
                path = f"memory/users/{user_id}/memory_{content_hash}.md"
            else:
                path = f"memory/shared/memory_{content_hash}.md"
        
        # Chunk content
        chunks = self.chunker.chunk_text(content)
        
        # Generate embeddings (if provider available)
        texts = [chunk.text for chunk in chunks]
        if self.embedding_provider:
            embeddings = self.embedding_provider.embed_batch(texts)
        else:
            # No embeddings, just use None
            embeddings = [None] * len(texts)
        
        # Create memory chunks
        memory_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = self._generate_chunk_id(path, chunk.start_line, chunk.end_line)
            chunk_hash = MemoryStorage.compute_hash(chunk.text)
            
            memory_chunks.append(MemoryChunk(
                id=chunk_id,
                user_id=user_id,
                scope=scope,
                source=source,
                path=path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                text=chunk.text,
                embedding=embedding,
                hash=chunk_hash,
                metadata=metadata
            ))
        
        # Save to storage
        self.storage.save_chunks_batch(memory_chunks)
        
        # Update file metadata
        file_hash = MemoryStorage.compute_hash(content)
        self.storage.update_file_metadata(
            path=path,
            source=source,
            file_hash=file_hash,
            mtime=int(os.path.getmtime(__file__)),  # Use current time
            size=len(content)
        )
    
    async def sync(self, force: bool = False):
        """
        Synchronize memory from files
        
        Args:
            force: Force full reindex
        """
        memory_dir = self.config.get_memory_dir()
        workspace_dir = self.config.get_workspace()
        
        # Scan MEMORY.md (workspace root)
        memory_file = Path(workspace_dir) / "MEMORY.md"
        if memory_file.exists():
            await self._sync_file(memory_file, "memory", "shared", None)
        
        # Scan memory directory (including daily summaries)
        if memory_dir.exists():
            for file_path in memory_dir.rglob("*.md"):
                # Determine scope and user_id from path
                rel_path = file_path.relative_to(workspace_dir)
                parts = rel_path.parts
                
                # Check if it's in daily summary directory
                if "daily" in parts:
                    # Daily summary files
                    if "users" in parts or len(parts) > 3:
                        # User-scoped daily summary: memory/daily/{user_id}/2024-01-29.md
                        user_idx = parts.index("daily") + 1
                        user_id = parts[user_idx] if user_idx < len(parts) else None
                        scope = "user"
                    else:
                        # Shared daily summary: memory/daily/2024-01-29.md
                        user_id = None
                        scope = "shared"
                elif "users" in parts:
                    # User-scoped memory
                    user_idx = parts.index("users") + 1
                    user_id = parts[user_idx] if user_idx < len(parts) else None
                    scope = "user"
                else:
                    # Shared memory
                    user_id = None
                    scope = "shared"
                
                await self._sync_file(file_path, "memory", scope, user_id)
        
        self._dirty = False
    
    async def _sync_file(
        self,
        file_path: Path,
        source: str,
        scope: str,
        user_id: Optional[str]
    ):
        """Sync a single file"""
        # Compute file hash
        content = file_path.read_text(encoding='utf-8')
        file_hash = MemoryStorage.compute_hash(content)
        
        # Get relative path
        workspace_dir = self.config.get_workspace()
        rel_path = str(file_path.relative_to(workspace_dir))
        
        # Check if file changed
        stored_hash = self.storage.get_file_hash(rel_path)
        if stored_hash == file_hash:
            return  # No changes
        
        # Delete old chunks
        self.storage.delete_by_path(rel_path)
        
        # Chunk and embed
        chunks = self.chunker.chunk_text(content)
        if not chunks:
            return
        
        texts = [chunk.text for chunk in chunks]
        if self.embedding_provider:
            embeddings = self.embedding_provider.embed_batch(texts)
        else:
            embeddings = [None] * len(texts)
        
        # Create memory chunks
        memory_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = self._generate_chunk_id(rel_path, chunk.start_line, chunk.end_line)
            chunk_hash = MemoryStorage.compute_hash(chunk.text)
            
            memory_chunks.append(MemoryChunk(
                id=chunk_id,
                user_id=user_id,
                scope=scope,
                source=source,
                path=rel_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                text=chunk.text,
                embedding=embedding,
                hash=chunk_hash,
                metadata=None
            ))
        
        # Save
        self.storage.save_chunks_batch(memory_chunks)
        
        # Update file metadata
        stat = file_path.stat()
        self.storage.update_file_metadata(
            path=rel_path,
            source=source,
            file_hash=file_hash,
            mtime=int(stat.st_mtime),
            size=stat.st_size
        )
    
    def flush_memory(
        self,
        messages: list,
        user_id: Optional[str] = None,
        reason: str = "threshold",
        max_messages: int = 10,
    ) -> bool:
        """
        Flush conversation summary to daily memory file.
        
        Args:
            messages: Conversation message list
            user_id: Optional user ID
            reason: "threshold" | "overflow" | "daily_summary"
            max_messages: Max recent messages to include (0 = all)
        
        Returns:
            True if content was written
        """
        success = self.flush_manager.flush_from_messages(
            messages=messages,
            user_id=user_id,
            reason=reason,
            max_messages=max_messages,
        )
        if success:
            self._dirty = True
        return success
    
    def get_status(self) -> Dict[str, Any]:
        """Get memory status"""
        stats = self.storage.get_stats()
        return {
            'chunks': stats['chunks'],
            'files': stats['files'],
            'workspace': str(self.config.get_workspace()),
            'dirty': self._dirty,
            'embedding_enabled': self.embedding_provider is not None,
            'embedding_provider': self.config.embedding_provider if self.embedding_provider else 'disabled',
            'embedding_model': self.config.embedding_model if self.embedding_provider else 'N/A',
            'search_mode': 'hybrid (vector + keyword)' if self.embedding_provider else 'keyword only (FTS5)'
        }
    
    def mark_dirty(self):
        """Mark memory as dirty (needs sync)"""
        self._dirty = True
    
    def close(self):
        """Close memory manager and release resources"""
        self.storage.close()
    
    # Helper methods
    
    def _generate_chunk_id(self, path: str, start_line: int, end_line: int) -> str:
        """Generate unique chunk ID"""
        content = f"{path}:{start_line}:{end_line}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _compute_temporal_decay(path: str, half_life_days: float = 30.0) -> float:
        """
        Compute temporal decay multiplier for dated memory files.
        
        Inspired by OpenClaw's temporal-decay: exponential decay based on file date.
        MEMORY.md and non-dated files are "evergreen" (no decay, multiplier=1.0).
        Daily files like memory/2025-03-01.md decay based on age.
        
        Formula: multiplier = exp(-ln2/half_life * age_in_days)
        """
        import re
        import math
        
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})\.md$', path)
        if not match:
            return 1.0  # evergreen: MEMORY.md, non-dated files
        
        try:
            file_date = datetime(
                int(match.group(1)), int(match.group(2)), int(match.group(3))
            )
            age_days = (datetime.now() - file_date).days
            if age_days <= 0:
                return 1.0
            
            decay_lambda = math.log(2) / half_life_days
            return math.exp(-decay_lambda * age_days)
        except (ValueError, OverflowError):
            return 1.0
    
    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        vector_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """Merge vector and keyword search results with temporal decay for dated files"""
        merged_map = {}
        
        for result in vector_results:
            key = (result.path, result.start_line, result.end_line)
            merged_map[key] = {
                'result': result,
                'vector_score': result.score,
                'keyword_score': 0.0
            }
        
        for result in keyword_results:
            key = (result.path, result.start_line, result.end_line)
            if key in merged_map:
                merged_map[key]['keyword_score'] = result.score
            else:
                merged_map[key] = {
                    'result': result,
                    'vector_score': 0.0,
                    'keyword_score': result.score
                }
        
        merged_results = []
        for entry in merged_map.values():
            combined_score = (
                vector_weight * entry['vector_score'] +
                keyword_weight * entry['keyword_score']
            )
            
            # Apply temporal decay for dated memory files
            result = entry['result']
            decay = self._compute_temporal_decay(result.path)
            combined_score *= decay
            
            merged_results.append(SearchResult(
                path=result.path,
                start_line=result.start_line,
                end_line=result.end_line,
                score=combined_score,
                snippet=result.snippet,
                source=result.source,
                user_id=result.user_id
            ))
        
        merged_results.sort(key=lambda r: r.score, reverse=True)
        return merged_results
