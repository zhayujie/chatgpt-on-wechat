"""
Memory service for handling memory query operations via cloud protocol.

Provides a unified interface for listing and reading memory files,
callable from the cloud client (LinkAI) or a future web console.

Memory file layout (under workspace_root):
    MEMORY.md               -> type: global
    memory/2026-02-20.md    -> type: daily
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from common.log import logger


class MemoryService:
    """
    High-level service for memory file queries.
    Operates directly on the filesystem — no MemoryManager dependency.
    """

    def __init__(self, workspace_root: str):
        """
        :param workspace_root: Workspace root directory (e.g. ~/cow)
        """
        self.workspace_root = workspace_root
        self.memory_dir = os.path.join(workspace_root, "memory")

    # ------------------------------------------------------------------
    # list — paginated file metadata
    # ------------------------------------------------------------------
    def list_files(self, page: int = 1, page_size: int = 20) -> dict:
        """
        List all memory files with metadata (without content).

        Returns::

            {
                "page": 1,
                "page_size": 20,
                "total": 15,
                "list": [
                    {"filename": "MEMORY.md", "type": "global", "size": 2048, "updated_at": "2026-02-20 10:00:00"},
                    {"filename": "2026-02-20.md", "type": "daily", "size": 512, "updated_at": "2026-02-20 09:30:00"},
                    ...
                ]
            }
        """
        files: List[dict] = []

        # 1. Global memory — MEMORY.md in workspace root
        global_path = os.path.join(self.workspace_root, "MEMORY.md")
        if os.path.isfile(global_path):
            files.append(self._file_info(global_path, "MEMORY.md", "global"))

        # 2. Daily memory files — memory/*.md (sorted newest first)
        if os.path.isdir(self.memory_dir):
            daily_files = []
            for name in os.listdir(self.memory_dir):
                full = os.path.join(self.memory_dir, name)
                if os.path.isfile(full) and name.endswith(".md"):
                    daily_files.append((name, full))
            # Sort by filename descending (newest date first)
            daily_files.sort(key=lambda x: x[0], reverse=True)
            for name, full in daily_files:
                files.append(self._file_info(full, name, "daily"))

        total = len(files)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        page_items = files[start:end]

        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "list": page_items,
        }

    # ------------------------------------------------------------------
    # content — read a single file
    # ------------------------------------------------------------------
    def get_content(self, filename: str) -> dict:
        """
        Read the full content of a memory file.

        :param filename: File name, e.g. ``MEMORY.md`` or ``2026-02-20.md``
        :return: dict with ``filename`` and ``content``
        :raises FileNotFoundError: if the file does not exist
        """
        path = self._resolve_path(filename)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Memory file not found: {filename}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "filename": filename,
            "content": content,
        }

    # ------------------------------------------------------------------
    # dispatch — single entry point for protocol messages
    # ------------------------------------------------------------------
    def dispatch(self, action: str, payload: Optional[dict] = None) -> dict:
        """
        Dispatch a memory management action.

        :param action: ``list`` or ``content``
        :param payload: action-specific payload
        :return: protocol-compatible response dict
        """
        payload = payload or {}
        try:
            if action == "list":
                page = payload.get("page", 1)
                page_size = payload.get("page_size", 20)
                result_payload = self.list_files(page=page, page_size=page_size)
                return {"action": action, "code": 200, "message": "success", "payload": result_payload}

            elif action == "content":
                filename = payload.get("filename")
                if not filename:
                    return {"action": action, "code": 400, "message": "filename is required", "payload": None}
                result_payload = self.get_content(filename)
                return {"action": action, "code": 200, "message": "success", "payload": result_payload}

            else:
                return {"action": action, "code": 400, "message": f"unknown action: {action}", "payload": None}

        except FileNotFoundError as e:
            return {"action": action, "code": 404, "message": str(e), "payload": None}
        except Exception as e:
            logger.error(f"[MemoryService] dispatch error: action={action}, error={e}")
            return {"action": action, "code": 500, "message": str(e), "payload": None}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _resolve_path(self, filename: str) -> str:
        """
        Resolve a filename to its absolute path.

        - ``MEMORY.md`` → ``{workspace_root}/MEMORY.md``
        - ``2026-02-20.md`` → ``{workspace_root}/memory/2026-02-20.md``
        """
        if filename == "MEMORY.md":
            return os.path.join(self.workspace_root, filename)
        return os.path.join(self.memory_dir, filename)

    @staticmethod
    def _file_info(path: str, filename: str, file_type: str) -> dict:
        """Build a file metadata dict."""
        stat = os.stat(path)
        updated_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "filename": filename,
            "type": file_type,
            "size": stat.st_size,
            "updated_at": updated_at,
        }
