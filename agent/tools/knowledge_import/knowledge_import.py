"""
Knowledge import tool.

Copies or moves uploaded files into knowledge/imports and triggers incremental
RAG indexing so the file becomes visible in the knowledge view.
"""

import asyncio
import os
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Dict

from agent.memory.document_parser import SUPPORTED_DOCUMENT_EXTENSIONS
from agent.tools.base_tool import BaseTool, ToolResult
from common.utils import expand_path


class KnowledgeImportTool(BaseTool):
    """Import an existing local file into knowledge/imports."""

    name: str = "knowledge_import"
    description: str = (
        "Import a local file into knowledge/imports so it becomes part of the "
        "knowledge base and RAG index. Use this for uploaded PDF/Word/Excel/"
        "Markdown/Text files that should be stored in the knowledge library."
    )
    params: dict = {
        "type": "object",
        "properties": {
            "source_path": {
                "type": "string",
                "description": "Existing local file path, typically an uploaded file under tmp/"
            },
            "target_subdir": {
                "type": "string",
                "description": "Optional subdirectory under knowledge/imports/ (e.g. 'sales/2026-q2')"
            },
            "filename": {
                "type": "string",
                "description": "Optional target filename. Keeps original extension if omitted."
            },
            "move": {
                "type": "boolean",
                "description": "Move the source file instead of copying it. Default: false",
                "default": False
            }
        },
        "required": ["source_path"]
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.memory_manager = self.config.get("memory_manager")

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        source_path = str(args.get("source_path", "")).strip()
        target_subdir = str(args.get("target_subdir", "")).strip().strip("/\\")
        filename = str(args.get("filename", "")).strip()
        move = bool(args.get("move", False))

        if not source_path:
            return ToolResult.fail("Error: source_path parameter is required")

        absolute_source = Path(expand_path(source_path)).resolve()
        if not absolute_source.exists() or not absolute_source.is_file():
            return ToolResult.fail(f"Error: source file not found: {source_path}")

        suffix = absolute_source.suffix.lower()
        if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
            return ToolResult.fail(
                f"Error: unsupported file type for knowledge import: {suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_DOCUMENT_EXTENSIONS))}"
            )

        workspace_root = self._get_workspace_root()
        if not workspace_root:
            return ToolResult.fail("Error: workspace root is not configured")

        safe_subdir = self._sanitize_subdir(target_subdir)
        target_dir = workspace_root / "knowledge" / "imports"
        if safe_subdir:
            target_dir = target_dir / safe_subdir
        target_dir.mkdir(parents=True, exist_ok=True)

        target_name = self._sanitize_filename(filename) if filename else absolute_source.name
        if not Path(target_name).suffix:
            target_name += suffix
        if Path(target_name).suffix.lower() != suffix:
            target_name = f"{Path(target_name).stem}{suffix}"

        target_path = self._dedupe_target_path(target_dir / target_name)

        try:
            if move:
                shutil.move(str(absolute_source), str(target_path))
            else:
                shutil.copy2(str(absolute_source), str(target_path))

            reindex_result = None
            if self.memory_manager:
                reindex_result = self._run_sync_imports()

            rel_path = target_path.relative_to(workspace_root).as_posix()
            result = {
                "message": f"Imported file into knowledge base: {rel_path}",
                "path": rel_path,
                "source_path": str(absolute_source),
                "doc_type": suffix.lstrip("."),
                "moved": move,
            }
            if reindex_result:
                result["indexing"] = reindex_result
            return ToolResult.success(result)
        except Exception as e:
            return ToolResult.fail(f"Error importing knowledge file: {str(e)}")

    def _run_sync_imports(self):
        """Run incremental imports sync from a sync tool context."""
        try:
            return asyncio.run(self.memory_manager.sync_imports(force=True))
        except RuntimeError:
            result_holder = {}
            error_holder = []

            def _runner():
                loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(loop)
                    result_holder["result"] = loop.run_until_complete(
                        self.memory_manager.sync_imports(force=True)
                    )
                except Exception as e:
                    error_holder.append(e)
                finally:
                    loop.close()

            thread = threading.Thread(target=_runner, daemon=True)
            thread.start()
            thread.join()
            if error_holder:
                raise error_holder[0]
            return result_holder.get("result")

    def _get_workspace_root(self) -> Path:
        if self.memory_manager:
            return self.memory_manager.config.get_workspace().resolve()
        cwd = self.config.get("cwd") or os.getcwd()
        return Path(expand_path(cwd)).resolve()

    @staticmethod
    def _sanitize_subdir(value: str) -> str:
        if not value:
            return ""
        normalized = value.replace("\\", "/").strip("/")
        normalized = re.sub(r"/+", "/", normalized)
        parts = []
        for part in normalized.split("/"):
            part = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff.]", "-", part).strip(".-")
            if not part or part in {".", ".."}:
                continue
            parts.append(part)
        return "/".join(parts)

    @staticmethod
    def _sanitize_filename(value: str) -> str:
        sanitized = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff.]", "-", value).strip(".-")
        return sanitized or "imported-file"

    @staticmethod
    def _dedupe_target_path(path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        index = 2
        while True:
            candidate = parent / f"{stem}-{index}{suffix}"
            if not candidate.exists():
                return candidate
            index += 1
