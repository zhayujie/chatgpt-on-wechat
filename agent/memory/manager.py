"""
Memory manager for AgentMesh

Provides high-level interface for memory operations
"""

import asyncio
import os
import re
import threading
from typing import List, Optional, Dict, Any
from pathlib import Path
import hashlib
from datetime import datetime

from agent.memory.config import MemoryConfig, get_default_memory_config
from agent.memory.storage import MemoryStorage, MemoryChunk, SearchResult
from agent.memory.chunker import TextChunker
from agent.memory.document_parser import DocumentParser, SUPPORTED_DOCUMENT_EXTENSIONS
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
        self.document_parser = DocumentParser()
        
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
                        from common.utils import get_cloud_headers
                        cloud_headers = get_cloud_headers(linkai_key)
                        cloud_headers.pop("Authorization", None)
                        self.embedding_provider = create_embedding_provider(
                            provider="linkai",
                            model=self.config.embedding_model,
                            api_key=linkai_key,
                            api_base=f"{linkai_base}/v1",
                            extra_headers=cloud_headers,
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
        self._imports_watch_thread: Optional[threading.Thread] = None
        self._imports_watch_stop = threading.Event()
    
    def _init_workspace(self):
        """Initialize workspace directories"""
        memory_dir = self.config.get_memory_dir()
        memory_dir.mkdir(parents=True, exist_ok=True)
        (self.config.get_workspace() / "knowledge" / "imports").mkdir(parents=True, exist_ok=True)
        
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
        retrieval_plan = self._build_retrieval_plan(query, max_results)
        
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
                    limit=retrieval_plan["vector_limit"],
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
            limit=retrieval_plan["keyword_limit"],
        )
        from common.log import logger
        logger.info(f"[MemoryManager] Keyword search found {len(keyword_results)} results for query: {query}")
        
        # Merge results
        merged = self._merge_results(
            vector_results,
            keyword_results,
            retrieval_plan["vector_weight"],
            retrieval_plan["keyword_weight"],
            query=query,
            query_type=retrieval_plan["query_type"],
        )
        
        # Filter by min score and diversify across documents so one file
        # does not crowd out other highly relevant sources.
        filtered = [r for r in merged if r.score >= min_score]
        diversified = self._diversify_results(
            filtered,
            max_results=max_results,
            query_type=retrieval_plan["query_type"],
        )
        return diversified[:max_results]
    
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
        chunks = self._chunk_document(content, path)
        
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
            
            chunk_metadata = dict(metadata or {})
            chunk_metadata.update(chunk.metadata)

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
                metadata=chunk_metadata
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
            await self._sync_file(memory_file, "memory", "shared", None, force=force)
        
        # Scan memory directory (including daily summaries)
        if memory_dir.exists():
            for file_path in memory_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                if file_path.suffix.lower() != ".md":
                    continue
                # Skip hidden directories (e.g. .dreams/)
                if any(part.startswith('.') for part in file_path.relative_to(workspace_dir).parts):
                    continue

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
                
                await self._sync_file(file_path, "memory", scope, user_id, force=force)

        # Scan knowledge directory (structured knowledge wiki + imported files)
        from config import conf
        if conf().get("knowledge", True):
            knowledge_dir = Path(workspace_dir) / "knowledge"
            if knowledge_dir.exists():
                for file_path in knowledge_dir.rglob("*"):
                    if not file_path.is_file():
                        continue
                    if file_path.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
                        continue
                    await self._sync_file(file_path, "knowledge", "shared", None, force=force)
        
        self._dirty = False

    async def sync_imports(self, force: bool = False) -> Dict[str, Any]:
        """Incrementally sync files under knowledge/imports and prune deleted files."""
        workspace_dir = self.config.get_workspace()
        imports_dir = workspace_dir / "knowledge" / "imports"
        imports_dir.mkdir(parents=True, exist_ok=True)

        indexed = 0
        current_paths = set()
        for file_path in imports_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in SUPPORTED_DOCUMENT_EXTENSIONS:
                continue
            rel_path = str(file_path.relative_to(workspace_dir)).replace("\\", "/")
            current_paths.add(rel_path)
            await self._sync_file(file_path, "knowledge", "shared", None, force=force)
            indexed += 1

        indexed_paths = set(self.storage.list_indexed_paths(prefix="knowledge/imports/", source="knowledge"))
        removed_paths = sorted(indexed_paths - current_paths)
        for rel_path in removed_paths:
            self.storage.delete_by_path(rel_path)
            self.storage.delete_file_record(rel_path)

        self._dirty = False
        return {
            "imports_dir": "knowledge/imports",
            "indexed_files": indexed,
            "removed_files": removed_paths,
            "watching": self._imports_watch_thread is not None and self._imports_watch_thread.is_alive(),
        }
    
    async def _sync_file(
        self,
        file_path: Path,
        source: str,
        scope: str,
        user_id: Optional[str],
        force: bool = False,
    ):
        """Sync a single file"""
        try:
            parsed_doc = self._parse_document_for_indexing(file_path, source)
        except ImportError as e:
            from common.log import logger
            logger.warning(f"[MemoryManager] Skip indexing {file_path.name}: {e}")
            return
        except Exception as e:
            from common.log import logger
            logger.warning(f"[MemoryManager] Failed to parse {file_path.name}: {e}")
            return
        content = parsed_doc.content
        if not content.strip():
            return

        # Compute file hash from raw bytes to reflect source file changes even if
        # parser normalization keeps extracted text stable.
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        
        # Get relative path
        workspace_dir = self.config.get_workspace()
        rel_path = str(file_path.relative_to(workspace_dir))
        
        # Check if file changed
        stored_hash = self.storage.get_file_hash(rel_path)
        if not force and stored_hash == file_hash:
            return  # No changes
        
        # Delete old chunks
        self.storage.delete_by_path(rel_path)
        
        # Chunk and embed
        chunks = self._chunk_document(content, rel_path, parsed_doc)
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
            
            chunk_metadata = self._build_chunk_metadata(
                rel_path=rel_path,
                source=source,
                chunk=chunk,
                content=content,
                parsed_doc=parsed_doc,
            )

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
                metadata=chunk_metadata
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
        context_summary_callback=None,
    ) -> bool:
        """
        Flush conversation summary to daily memory file.

        Args:
            messages: Conversation message list
            user_id: Optional user ID
            reason: "threshold" | "overflow" | "daily_summary"
            max_messages: Max recent messages to include (0 = all)
            context_summary_callback: Optional callback(str) invoked with the
                daily summary text for in-context injection

        Returns:
            True if flush was dispatched
        """
        success = self.flush_manager.flush_from_messages(
            messages=messages,
            user_id=user_id,
            reason=reason,
            max_messages=max_messages,
            context_summary_callback=context_summary_callback,
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
            'imports_dir': 'knowledge/imports',
            'imports_watching': self._imports_watch_thread is not None and self._imports_watch_thread.is_alive(),
            'embedding_enabled': self.embedding_provider is not None,
            'embedding_provider': self.config.embedding_provider if self.embedding_provider else 'disabled',
            'embedding_model': self.config.embedding_model if self.embedding_provider else 'N/A',
            'search_mode': 'hybrid (vector + keyword)' if self.embedding_provider else 'keyword only (FTS5)',
            'knowledge_supported_formats': sorted(SUPPORTED_DOCUMENT_EXTENSIONS),
        }
    
    def mark_dirty(self):
        """Mark memory as dirty (needs sync)"""
        self._dirty = True

    def start_import_watcher(self):
        """Start a background poller for knowledge/imports incremental indexing."""
        if not self.config.imports_watch_enabled:
            return
        if self._imports_watch_thread and self._imports_watch_thread.is_alive():
            return

        self._imports_watch_stop.clear()

        def _watch_loop():
            from common.log import logger

            logger.info("[MemoryManager] knowledge/imports watcher started")
            while not self._imports_watch_stop.wait(self.config.imports_watch_interval_sec):
                try:
                    asyncio.run(self.sync_imports(force=False))
                except Exception as e:
                    logger.warning(f"[MemoryManager] knowledge/imports watcher error: {e}")
            logger.info("[MemoryManager] knowledge/imports watcher stopped")

        self._imports_watch_thread = threading.Thread(
            target=_watch_loop,
            name="knowledge-imports-watcher",
            daemon=True,
        )
        self._imports_watch_thread.start()

    def stop_import_watcher(self):
        """Stop the knowledge/imports watcher thread."""
        self._imports_watch_stop.set()
        if self._imports_watch_thread and self._imports_watch_thread.is_alive():
            self._imports_watch_thread.join(timeout=1.0)
        self._imports_watch_thread = None
    
    def close(self):
        """Close memory manager and release resources"""
        self.stop_import_watcher()
        self.storage.close()

    def normalize_requested_path(self, path: str) -> str:
        """Normalize a user-supplied memory/knowledge path inside the workspace."""
        if not path:
            raise ValueError("path is required")

        normalized = path.replace("\\", "/").strip()
        if (
            not normalized.startswith("memory/")
            and not normalized.startswith("knowledge/")
            and not normalized.startswith("/")
            and normalized != "MEMORY.md"
        ):
            normalized = f"memory/{normalized}"
        return normalized

    def resolve_workspace_path(self, path: str) -> tuple[str, Path]:
        """Resolve a normalized path and ensure it stays inside the workspace."""
        normalized = self.normalize_requested_path(path)
        workspace_dir = self.config.get_workspace().resolve()
        file_path = (workspace_dir / normalized).resolve()
        if file_path != workspace_dir and workspace_dir not in file_path.parents:
            raise ValueError("Access denied: path outside workspace")
        return normalized, file_path

    def inspect_document_chunks(self, path: str) -> Dict[str, Any]:
        """Parse and chunk a document for UI inspection and citation generation."""
        rel_path, file_path = self.resolve_workspace_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {rel_path}")

        parsed_doc = self._parse_document_for_indexing(file_path, "knowledge" if rel_path.startswith("knowledge/") else "memory")
        chunks = self._chunk_document(parsed_doc.content, rel_path, parsed_doc=parsed_doc)
        chunk_items = []
        for index, chunk in enumerate(chunks, start=1):
            chunk_metadata = self._build_chunk_metadata(
                rel_path=rel_path,
                source="knowledge" if rel_path.startswith("knowledge/") else "memory",
                chunk=chunk,
                content=parsed_doc.content,
                parsed_doc=parsed_doc,
            )
            chunk_items.append(
                {
                    "index": index,
                    "path": rel_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "citation": chunk_metadata.get("citation", ""),
                    "page_number": chunk_metadata.get("page_number"),
                    "section_title": chunk_metadata.get("section_title", ""),
                    "section_path": chunk_metadata.get("section_path", ""),
                    "title": chunk_metadata.get("title", ""),
                    "category": chunk_metadata.get("category", ""),
                    "doc_type": chunk_metadata.get("doc_type", parsed_doc.doc_type),
                    "chunk_mode": chunk_metadata.get("chunk_mode", parsed_doc.chunk_mode),
                    "metadata": chunk_metadata,
                    "content": chunk.text,
                    "preview": chunk.text[:320] + ("..." if len(chunk.text) > 320 else ""),
                }
            )

        return {
            "path": rel_path,
            "doc_type": parsed_doc.doc_type,
            "chunk_mode": parsed_doc.chunk_mode,
            "title": parsed_doc.metadata.get("title"),
            "total_chunks": len(chunk_items),
            "chunks": chunk_items,
        }

    def read_document_range(self, path: str, start_line: int = 1, num_lines: Optional[int] = None) -> Dict[str, Any]:
        """Read a normalized document slice and attach stable citation metadata."""
        rel_path, file_path = self.resolve_workspace_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {rel_path}")

        parsed_doc = self._parse_document_for_indexing(file_path, "knowledge" if rel_path.startswith("knowledge/") else "memory")
        lines = parsed_doc.content.split("\n")
        total_lines = len(lines)
        if start_line < 1:
            start_line = 1
        start_idx = start_line - 1
        end_idx = total_lines if not num_lines else min(total_lines, start_idx + max(num_lines, 0))
        selected_lines = lines[start_idx:end_idx]
        end_line = start_line + max(len(selected_lines) - 1, 0)

        chunk_info = self.inspect_document_chunks(rel_path)
        selected_chunk = None
        best_overlap = -1
        for chunk in chunk_info["chunks"]:
            overlap = min(end_line, chunk["end_line"]) - max(start_line, chunk["start_line"]) + 1
            if overlap > best_overlap:
                best_overlap = overlap
                selected_chunk = chunk

        metadata = dict((selected_chunk or {}).get("metadata") or {})
        if "citation" not in metadata:
            metadata["citation"] = self.build_citation(rel_path, start_line, end_line, metadata)

        return {
            "path": rel_path,
            "doc_type": parsed_doc.doc_type,
            "chunk_mode": parsed_doc.chunk_mode,
            "title": parsed_doc.metadata.get("title"),
            "content": "\n".join(selected_lines),
            "start_line": start_line,
            "end_line": end_line,
            "shown_lines": len(selected_lines),
            "total_lines": total_lines,
            "citation": metadata.get("citation", ""),
            "metadata": metadata,
        }
    
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
        keyword_weight: float,
        query: str = "",
        query_type: str = "general",
    ) -> List[SearchResult]:
        """Merge and rerank search results with temporal and source-aware scoring."""
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

            rerank_bonus = self._compute_rerank_bonus(
                result=result,
                query=query,
                query_type=query_type,
                vector_score=entry['vector_score'],
                keyword_score=entry['keyword_score'],
            )
            final_score = combined_score + rerank_bonus
            
            merged_results.append(SearchResult(
                path=result.path,
                start_line=result.start_line,
                end_line=result.end_line,
                score=final_score,
                snippet=result.snippet,
                source=result.source,
                user_id=result.user_id,
                metadata=result.metadata,
            ))
        
        merged_results.sort(key=lambda r: r.score, reverse=True)
        return merged_results

    @staticmethod
    def _target_unique_paths(max_results: int, query_type: str) -> int:
        """Determine how many distinct documents to prioritize in top hits."""
        if max_results <= 1:
            return 1
        if query_type in {"location", "exact"}:
            return min(2, max_results)
        return min(3, max_results)

    def _diversify_results(
        self,
        results: List[SearchResult],
        max_results: int,
        query_type: str,
    ) -> List[SearchResult]:
        """
        Prefer multiple distinct files in top results before adding extra
        chunks from the same document. This helps the agent inspect parallel
        manuals/checklists instead of stopping at the first matching file.
        """
        if not results or max_results <= 1:
            return results[:max_results]

        target_unique_paths = self._target_unique_paths(max_results, query_type)
        per_path_cap = 2 if max_results > 2 else 1

        chosen: List[SearchResult] = []
        path_counts: Dict[str, int] = {}

        # Pass 1: collect the best hit from as many different paths as possible.
        for result in results:
            if path_counts.get(result.path, 0) > 0:
                continue
            chosen.append(result)
            path_counts[result.path] = 1
            if len(chosen) >= min(target_unique_paths, max_results):
                break

        # Pass 2: fill remaining slots, but cap repeated chunks per path.
        for result in results:
            if len(chosen) >= max_results:
                break
            if path_counts.get(result.path, 0) >= per_path_cap:
                continue
            if any(
                existing.path == result.path
                and existing.start_line == result.start_line
                and existing.end_line == result.end_line
                for existing in chosen
            ):
                continue
            chosen.append(result)
            path_counts[result.path] = path_counts.get(result.path, 0) + 1

        return chosen

    def _chunk_document(self, content: str, rel_path: str, parsed_doc=None):
        """Chunk a document with source-aware metadata and parser-specific strategy."""
        if parsed_doc is None:
            base_metadata = self._build_document_metadata(rel_path, content)
            chunk_mode = "markdown" if rel_path.endswith(".md") else "plain_text"
        else:
            base_metadata = self._build_document_metadata(rel_path, content, parsed_doc=parsed_doc)
            chunk_mode = parsed_doc.chunk_mode
        return self.chunker.chunk_document(content, chunk_mode=chunk_mode, metadata=base_metadata)

    def _build_document_metadata(self, rel_path: str, content: str, parsed_doc=None) -> Dict[str, Any]:
        """Build document-level metadata used for chunk indexing and reranking."""
        first_heading = ""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                first_heading = stripped[2:].strip()
                break

        path_obj = Path(rel_path)
        source_type = self._detect_source_type(rel_path)
        category = path_obj.parent.name if len(path_obj.parts) > 1 else source_type
        title = None
        if parsed_doc:
            title = parsed_doc.metadata.get("title")
        title = title or first_heading or path_obj.stem.replace("-", " ").replace("_", " ").strip() or path_obj.name

        metadata = {
            "title": title,
            "source_type": source_type,
            "category": category,
            "is_evergreen": source_type in {"memory_core", "knowledge_page"},
        }
        if parsed_doc:
            metadata.update(parsed_doc.metadata)
            metadata["doc_type"] = parsed_doc.doc_type
            metadata["chunk_mode"] = parsed_doc.chunk_mode
        return metadata

    def _build_chunk_metadata(
        self,
        rel_path: str,
        source: str,
        chunk,
        content: str,
        parsed_doc=None,
    ) -> Dict[str, Any]:
        """Merge document metadata with chunk-level metadata."""
        doc_metadata = self._build_document_metadata(rel_path, content, parsed_doc=parsed_doc)
        chunk_metadata = dict(doc_metadata)
        chunk_metadata.update(chunk.metadata or {})
        chunk_metadata["source"] = source
        return self._attach_reference_metadata(
            rel_path=rel_path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            metadata=chunk_metadata,
        )

    @staticmethod
    def _extract_page_number(metadata: Dict[str, Any]) -> Optional[int]:
        """Infer page number from parsed metadata and section titles."""
        page_number = metadata.get("page_number")
        if isinstance(page_number, int):
            return page_number

        for candidate in (metadata.get("section_title"), metadata.get("title")):
            if not candidate:
                continue
            match = re.search(r"\bpage\s+(\d+)\b", str(candidate), re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _attach_reference_metadata(
        self,
        rel_path: str,
        start_line: int,
        end_line: int,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize section/page metadata and attach a stable citation string."""
        normalized = dict(metadata or {})
        page_number = self._extract_page_number(normalized)
        if page_number is not None:
            normalized["page_number"] = page_number

        parent_titles = normalized.get("parent_titles") or []
        if isinstance(parent_titles, list):
            section_bits = [str(item).strip() for item in parent_titles if str(item).strip()]
        else:
            section_bits = [str(parent_titles).strip()] if str(parent_titles).strip() else []
        section_title = str(normalized.get("section_title", "")).strip()
        if section_title:
            section_bits.append(section_title)
        section_path = " > ".join(section_bits)
        if section_path:
            normalized["section_path"] = section_path

        normalized["citation"] = self.build_citation(
            path=rel_path,
            start_line=start_line,
            end_line=end_line,
            metadata=normalized,
        )
        return normalized

    def build_citation(
        self,
        path: str,
        start_line: int,
        end_line: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a stable inline citation string for final answers and tools."""
        metadata = metadata or {}
        anchors = []
        page_number = self._extract_page_number(metadata)
        if page_number is not None:
            anchors.append(f"page={page_number}")

        section_path = str(metadata.get("section_path") or metadata.get("section_title") or "").strip()
        if section_path:
            safe_section = re.sub(r"\s+", "-", section_path)
            safe_section = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff>]", "", safe_section)
            if safe_section:
                anchors.append(f"section={safe_section}")

        anchors.append(f"L{start_line}-L{end_line}")
        return f"[{path}#{'#'.join(anchors)}]"

    @staticmethod
    def _detect_source_type(rel_path: str) -> str:
        """Infer source type from path."""
        normalized = rel_path.replace("\\", "/")
        if normalized == "MEMORY.md" or normalized.endswith("/MEMORY.md"):
            return "memory_core"
        if normalized.startswith("knowledge/"):
            return "knowledge_page"
        if "/dreams/" in normalized or normalized.startswith("memory/dreams/"):
            return "memory_dream"
        if re.search(r"\d{4}-\d{2}-\d{2}\.md$", normalized):
            return "memory_daily"
        if normalized.startswith("memory/users/"):
            return "memory_user"
        return "memory_note"

    def _parse_document_for_indexing(self, file_path: Path, source: str):
        """Parse a source file into normalized content for indexing."""
        workspace_dir = self.config.get_workspace()
        rel_path = str(file_path.relative_to(workspace_dir)).replace("\\", "/")
        return self.document_parser.parse(file_path, rel_path)

    def _build_retrieval_plan(self, query: str, max_results: int) -> Dict[str, Any]:
        """Classify the query and derive retrieval weights/limits."""
        query_type = self._classify_query(query)
        vector_weight = self.config.vector_weight
        keyword_weight = self.config.keyword_weight

        if query_type == "recent_memory":
            vector_weight = 0.55
            keyword_weight = 0.45
        elif query_type == "core_memory":
            vector_weight = 0.50
            keyword_weight = 0.50
        elif query_type == "knowledge":
            vector_weight = 0.75
            keyword_weight = 0.25
        elif query_type == "exact_lookup":
            vector_weight = 0.35
            keyword_weight = 0.65

        candidate_limit = max(max_results * 3, 12)
        return {
            "query_type": query_type,
            "vector_weight": vector_weight,
            "keyword_weight": keyword_weight,
            "vector_limit": candidate_limit,
            "keyword_limit": candidate_limit,
        }

    @staticmethod
    def _classify_query(query: str) -> str:
        """Lightweight query classifier for source-aware retrieval."""
        normalized = query.lower()

        recent_patterns = ["昨天", "刚才", "最近", "前几天", "上次", "today", "yesterday", "recent", "earlier"]
        core_patterns = ["偏好", "习惯", "记住", "总是", "不要", "preference", "prefer", "always", "never"]
        knowledge_patterns = ["什么是", "原理", "概念", "总结", "架构", "how", "what is", "concept", "architecture"]
        exact_patterns = ["文件", "文档", "标题", ".md", "path", "file", "document", "title"]

        if any(token in normalized for token in recent_patterns):
            return "recent_memory"
        if any(token in normalized for token in core_patterns):
            return "core_memory"
        if any(token in normalized for token in knowledge_patterns):
            return "knowledge"
        if any(token in normalized for token in exact_patterns) or "/" in normalized:
            return "exact_lookup"
        return "general"

    def _compute_rerank_bonus(
        self,
        result: SearchResult,
        query: str,
        query_type: str,
        vector_score: float,
        keyword_score: float,
    ) -> float:
        """Apply lightweight source-aware reranking."""
        metadata = result.metadata or {}
        source_type = metadata.get("source_type", "")
        title = str(metadata.get("title", "")).lower()
        section_title = str(metadata.get("section_title", "")).lower()
        category = str(metadata.get("category", "")).lower()
        normalized_query = query.lower()
        query_terms = [term for term in re.findall(r"[\w\u4e00-\u9fff]{2,}", normalized_query) if term]

        bonus = 0.0

        if source_type == "memory_core":
            bonus += 0.14 if query_type == "core_memory" else 0.03
        elif source_type == "memory_daily":
            bonus += 0.14 if query_type == "recent_memory" else 0.02
        elif source_type == "knowledge_page":
            bonus += 0.16 if query_type == "knowledge" else 0.04

        title_hits = sum(1 for term in query_terms if term in title)
        section_hits = sum(1 for term in query_terms if term in section_title)
        category_hits = sum(1 for term in query_terms if term in category)

        bonus += min(title_hits * 0.06, 0.18)
        bonus += min(section_hits * 0.04, 0.12)
        bonus += min(category_hits * 0.03, 0.06)

        if result.path.lower() in normalized_query or title and title in normalized_query:
            bonus += 0.08

        if vector_score > 0 and keyword_score > 0:
            bonus += 0.05

        parent_titles = metadata.get("parent_titles") or []
        if isinstance(parent_titles, list):
            for parent in parent_titles:
                if any(term in str(parent).lower() for term in query_terms):
                    bonus += 0.02
                    break

        return bonus
