"""
Knowledge service for handling knowledge base operations.

Provides a unified interface for listing, reading, graphing, chunk inspection,
and import reindexing for files under the workspace knowledge directory.
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Optional

from agent.memory.config import MemoryConfig
from agent.memory.document_parser import SUPPORTED_DOCUMENT_EXTENSIONS
from agent.memory.manager import MemoryManager
from common.log import logger
from config import conf


class KnowledgeService:
    """High-level service for knowledge base queries."""

    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.knowledge_dir = os.path.join(workspace_root, "knowledge")
        self._memory_manager: Optional[MemoryManager] = None

    @property
    def memory_manager(self) -> MemoryManager:
        """Lazy-init memory manager for parser/chunker/reindex reuse."""
        if self._memory_manager is None:
            self._memory_manager = MemoryManager(MemoryConfig(workspace_root=self.workspace_root))
        return self._memory_manager

    def list_tree(self) -> dict:
        """Return the knowledge directory tree grouped by category."""
        if not os.path.isdir(self.knowledge_dir):
            return {
                "tree": [],
                "stats": {"pages": 0, "size": 0},
                "enabled": conf().get("knowledge", True),
                "imports_dir": "knowledge/imports",
            }

        stats = {"pages": 0, "size": 0}
        root_files, tree = self._scan_dir(self.knowledge_dir, stats, is_root=True)
        return {
            "root_files": root_files,
            "tree": tree,
            "stats": stats,
            "enabled": conf().get("knowledge", True),
            "imports_dir": "knowledge/imports",
        }

    def _scan_dir(self, dir_path: str, stats: dict, is_root: bool = False) -> tuple:
        """Recursively scan a directory and return files + child directories."""
        files = []
        children = []
        for name in sorted(os.listdir(dir_path)):
            if name.startswith("."):
                continue
            full = os.path.join(dir_path, name)
            if os.path.isdir(full):
                sub_files, sub_children = self._scan_dir(full, stats)
                children.append({"dir": name, "files": sub_files, "children": sub_children})
                continue

            suffix = Path(full).suffix.lower()
            if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
                continue

            size = os.path.getsize(full)
            if not is_root:
                stats["pages"] += 1
                stats["size"] += size

            rel_path = str(Path(full).relative_to(self.knowledge_dir)).replace("\\", "/")
            title = Path(full).stem.replace("-", " ").replace("_", " ").strip() or name
            try:
                if suffix in {".md", ".markdown", ".txt", ".rst"}:
                    parsed = self.memory_manager.document_parser.parse(Path(full), f"knowledge/{rel_path}")
                    title = parsed.metadata.get("title") or title
            except Exception:
                pass

            files.append(
                {
                    "name": name,
                    "title": title,
                    "size": size,
                    "doc_type": suffix.lstrip("."),
                }
            )
        return files, children

    def read_file(self, rel_path: str) -> dict:
        """Read a single knowledge file and return normalized text content."""
        full_path = self._resolve_knowledge_path(rel_path)
        result = self.memory_manager.read_document_range(f"knowledge/{rel_path}", start_line=1, num_lines=None)
        return {
            "content": result["content"],
            "path": rel_path,
            "title": result.get("title"),
            "doc_type": result.get("doc_type"),
            "chunk_mode": result.get("chunk_mode"),
            "citation": result.get("citation"),
            "total_lines": result.get("total_lines"),
            "file_size": os.path.getsize(full_path),
        }

    def get_chunks(self, rel_path: str) -> dict:
        """Inspect live RAG chunks for a knowledge document."""
        self._resolve_knowledge_path(rel_path)
        chunk_info = self.memory_manager.inspect_document_chunks(f"knowledge/{rel_path}")
        chunk_info["path"] = rel_path
        return chunk_info

    def create_file(
        self,
        title: str,
        rel_path: Optional[str] = None,
        content: str = "",
    ) -> dict:
        """Create a new markdown knowledge page and index it."""
        title = (title or "").strip()
        if not title and not rel_path:
            raise ValueError("title is required")

        rel_path = (rel_path or "").strip().replace("\\", "/").strip("/")
        if rel_path and ".." in rel_path:
            raise ValueError("invalid path")

        if not rel_path:
            slug = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "-", title).strip("-").lower() or "untitled"
            rel_path = f"notes/{slug}.md"
        elif not rel_path.endswith(".md"):
            rel_path += ".md"

        full_path = os.path.normpath(os.path.join(self.knowledge_dir, rel_path))
        allowed = os.path.normpath(self.knowledge_dir)
        if not full_path.startswith(allowed + os.sep):
            raise ValueError("path outside knowledge dir")
        if os.path.exists(full_path):
            raise ValueError(f"file already exists: {rel_path}")

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        body = content.strip()
        markdown = f"# {title or Path(rel_path).stem}\n\n{body}\n" if body else f"# {title or Path(rel_path).stem}\n"
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        asyncio.run(self.memory_manager.sync(force=False))
        return {"path": rel_path, "title": title or Path(rel_path).stem}

    def delete_file(self, rel_path: str) -> dict:
        """Delete a knowledge file and purge its index entries."""
        full_path = self._resolve_knowledge_path(rel_path)
        os.remove(full_path)
        indexed_path = f"knowledge/{rel_path}".replace("\\", "/")
        self.memory_manager.storage.delete_by_path(indexed_path)
        self.memory_manager.storage.delete_file_record(indexed_path)
        return {"path": rel_path, "deleted": True}

    def reindex_imports(self, force: bool = True) -> dict:
        """Trigger a manual reindex for knowledge/imports."""
        result = asyncio.run(self.memory_manager.sync_imports(force=force))
        return result

    def build_graph(self) -> dict:
        """Parse markdown knowledge pages and extract cross-reference links."""
        knowledge_path = Path(self.knowledge_dir)
        if not knowledge_path.is_dir():
            return {"nodes": [], "links": []}

        nodes = {}
        links = []
        link_re = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)\)")

        for md_file in knowledge_path.rglob("*.md"):
            rel = str(md_file.relative_to(knowledge_path)).replace("\\", "/")
            if rel in ("index.md", "log.md"):
                continue
            parts = rel.split("/")
            category = parts[0] if len(parts) > 1 else "root"
            title = md_file.stem.replace("-", " ").title()
            try:
                content = md_file.read_text(encoding="utf-8")
                first_line = content.strip().split("\n")[0]
                if first_line.startswith("# "):
                    title = first_line[2:].strip()
                for _, link_target in link_re.findall(content):
                    resolved = (md_file.parent / link_target).resolve()
                    try:
                        target_rel = str(resolved.relative_to(knowledge_path)).replace("\\", "/")
                    except ValueError:
                        continue
                    if target_rel != rel:
                        links.append({"source": rel, "target": target_rel})
            except Exception:
                pass
            nodes[rel] = {"id": rel, "label": title, "category": category}

        valid_ids = set(nodes.keys())
        deduped = []
        seen = set()
        for link in links:
            if link["source"] not in valid_ids or link["target"] not in valid_ids:
                continue
            key = tuple(sorted((link["source"], link["target"])))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(link)

        return {"nodes": list(nodes.values()), "links": deduped}

    def dispatch(self, action: str, payload: Optional[dict] = None) -> dict:
        """Dispatch a knowledge management action."""
        payload = payload or {}
        try:
            if action == "list":
                result = self.list_tree()
                return {"action": action, "code": 200, "message": "success", "payload": result}

            if action == "read":
                path = payload.get("path")
                if not path:
                    return {"action": action, "code": 400, "message": "path is required", "payload": None}
                result = self.read_file(path)
                return {"action": action, "code": 200, "message": "success", "payload": result}

            if action == "chunks":
                path = payload.get("path")
                if not path:
                    return {"action": action, "code": 400, "message": "path is required", "payload": None}
                result = self.get_chunks(path)
                return {"action": action, "code": 200, "message": "success", "payload": result}

            if action == "create":
                result = self.create_file(
                    title=payload.get("title", ""),
                    rel_path=payload.get("path"),
                    content=payload.get("content", ""),
                )
                return {"action": action, "code": 200, "message": "success", "payload": result}

            if action == "delete":
                path = payload.get("path")
                if not path:
                    return {"action": action, "code": 400, "message": "path is required", "payload": None}
                result = self.delete_file(path)
                return {"action": action, "code": 200, "message": "success", "payload": result}

            if action == "reindex_imports":
                result = self.reindex_imports(force=bool(payload.get("force", True)))
                return {"action": action, "code": 200, "message": "success", "payload": result}

            if action == "graph":
                result = self.build_graph()
                return {"action": action, "code": 200, "message": "success", "payload": result}

            return {"action": action, "code": 400, "message": f"unknown action: {action}", "payload": None}

        except ValueError as e:
            return {"action": action, "code": 403, "message": str(e), "payload": None}
        except FileNotFoundError as e:
            return {"action": action, "code": 404, "message": str(e), "payload": None}
        except Exception as e:
            logger.error(f"[KnowledgeService] dispatch error: action={action}, error={e}")
            return {"action": action, "code": 500, "message": str(e), "payload": None}

    def _resolve_knowledge_path(self, rel_path: str) -> str:
        """Resolve and validate a path inside knowledge/."""
        if not rel_path or ".." in rel_path:
            raise ValueError("invalid path")

        full_path = os.path.normpath(os.path.join(self.knowledge_dir, rel_path))
        allowed = os.path.normpath(self.knowledge_dir)
        if not full_path.startswith(allowed + os.sep) and full_path != allowed:
            raise ValueError("path outside knowledge dir")
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"file not found: {rel_path}")
        return full_path
