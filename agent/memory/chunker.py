"""
Text chunking utilities for memory and knowledge documents.

Provides both a generic line-based chunker and a lightweight Markdown-aware
chunker that preserves heading structure for better retrieval quality.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TextChunk:
    """Represents a text chunk with line numbers and retrieval metadata."""

    text: str
    start_line: int
    end_line: int
    metadata: Dict[str, object] = field(default_factory=dict)


class TextChunker:
    """Chunks text by line count with optional Markdown structure awareness."""

    def __init__(self, max_tokens: int = 500, overlap_tokens: int = 50):
        """
        Initialize chunker.

        Args:
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap tokens between chunks
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        # Rough estimation: ~4 chars per token for English/Chinese mixed
        self.chars_per_token = 4

    def chunk_text(
        self,
        text: str,
        start_line: int = 1,
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[TextChunk]:
        """
        Chunk plain text into overlapping segments.

        Args:
            text: Input text to chunk
            start_line: Starting line number of the given text in the source doc
            metadata: Metadata attached to every emitted chunk
        """
        return self._chunk_lines(text.split("\n"), start_line=start_line, metadata=metadata)

    def chunk_markdown(
        self,
        text: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[TextChunk]:
        """
        Chunk Markdown text while respecting heading structure.

        The algorithm keeps section blocks together when possible and propagates
        section path metadata for better ranking and citation quality.
        """
        if not text.strip():
            return []

        lines = text.split("\n")
        base_metadata = dict(metadata or {})

        heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
        sections = []
        heading_stack: List[tuple[int, str]] = []
        current_lines: List[str] = []
        current_start_line = 1
        current_path: List[str] = []

        def flush_current(end_line: int):
            if not current_lines:
                return

            section_metadata = dict(base_metadata)
            section_title = current_path[-1] if current_path else section_metadata.get("title", "")
            parent_titles = current_path[:-1] if len(current_path) > 1 else []
            section_metadata.update(
                {
                    "section_title": section_title,
                    "parent_titles": parent_titles,
                    "heading_path": list(current_path),
                    "chunk_type": "markdown_section" if current_path else "markdown_root",
                }
            )
            sections.append(
                (current_lines[:], current_start_line, end_line, section_metadata)
            )

        for lineno, line in enumerate(lines, start=1):
            match = heading_re.match(line)
            if match:
                flush_current(lineno - 1)

                level = len(match.group(1))
                heading_text = match.group(2).strip()
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, heading_text))

                current_path = [item[1] for item in heading_stack]
                current_lines = [line]
                current_start_line = lineno
            else:
                if not current_lines:
                    current_lines = [line]
                    current_start_line = lineno
                else:
                    current_lines.append(line)

        flush_current(len(lines))

        chunks: List[TextChunk] = []
        for section_lines, section_start, _section_end, section_metadata in sections:
            chunks.extend(
                self._chunk_lines(
                    section_lines,
                    start_line=section_start,
                    metadata=section_metadata,
                )
            )

        if chunks:
            return chunks

        return self.chunk_text(text, metadata=base_metadata)

    def chunk_document(
        self,
        text: str,
        chunk_mode: str = "plain_text",
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[TextChunk]:
        """
        Chunk a normalized document according to its format strategy.

        Supported modes:
        - markdown: preserve heading hierarchy
        - pdf_pages: each `# Page N` section becomes a primary unit
        - word_sections: heading-aware paragraph chunking
        - spreadsheet: chunk per sheet/row windows
        - plain_text: generic overlap chunking
        """
        if chunk_mode in {"markdown", "pdf_pages", "word_sections"}:
            return self.chunk_markdown(text, metadata=metadata)
        if chunk_mode == "spreadsheet":
            return self._chunk_spreadsheet(text, metadata=metadata)
        return self.chunk_text(text, metadata=metadata)

    def _chunk_lines(
        self,
        lines: List[str],
        start_line: int = 1,
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[TextChunk]:
        """Internal line-aware chunking with overlap and metadata propagation."""
        if not any(line.strip() for line in lines):
            return []

        metadata = dict(metadata or {})
        chunks: List[TextChunk] = []

        max_chars = self.max_tokens * self.chars_per_token
        overlap_chars = self.overlap_tokens * self.chars_per_token

        current_chunk: List[str] = []
        current_chars = 0
        chunk_start_line = start_line

        for offset, line in enumerate(lines):
            absolute_line = start_line + offset
            line_chars = len(line)

            if line_chars > max_chars:
                if current_chunk:
                    chunks.append(
                        TextChunk(
                            text="\n".join(current_chunk),
                            start_line=chunk_start_line,
                            end_line=absolute_line - 1,
                            metadata=dict(metadata),
                        )
                    )
                    current_chunk = []
                    current_chars = 0

                for sub_index, sub_chunk in enumerate(self._split_long_line(line, max_chars)):
                    sub_metadata = dict(metadata)
                    sub_metadata["chunk_type"] = sub_metadata.get("chunk_type", "text_chunk")
                    sub_metadata["split_part"] = sub_index + 1
                    chunks.append(
                        TextChunk(
                            text=sub_chunk,
                            start_line=absolute_line,
                            end_line=absolute_line,
                            metadata=sub_metadata,
                        )
                    )
                chunk_start_line = absolute_line + 1
                continue

            if current_chars + line_chars > max_chars and current_chunk:
                chunks.append(
                    TextChunk(
                        text="\n".join(current_chunk),
                        start_line=chunk_start_line,
                        end_line=absolute_line - 1,
                        metadata=dict(metadata),
                    )
                )

                overlap_lines = self._get_overlap_lines(current_chunk, overlap_chars)
                current_chunk = overlap_lines + [line]
                current_chars = sum(len(item) for item in current_chunk)
                chunk_start_line = absolute_line - len(overlap_lines)
            else:
                current_chunk.append(line)
                current_chars += line_chars

        if current_chunk:
            chunks.append(
                TextChunk(
                    text="\n".join(current_chunk),
                    start_line=chunk_start_line,
                    end_line=start_line + len(lines) - 1,
                    metadata=dict(metadata),
                )
            )

        return chunks

    def _chunk_spreadsheet(
        self,
        text: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[TextChunk]:
        """Chunk spreadsheet text by sheet boundaries, then by row windows."""
        if not text.strip():
            return []

        lines = text.split("\n")
        sheet_ranges = []
        current_start = 1
        current_sheet = ""

        for lineno, line in enumerate(lines, start=1):
            if line.startswith("# Sheet:"):
                if lineno > current_start:
                    sheet_ranges.append((current_sheet, current_start, lineno - 1))
                current_sheet = line.replace("# Sheet:", "", 1).strip()
                current_start = lineno

        sheet_ranges.append((current_sheet, current_start, len(lines)))

        chunks: List[TextChunk] = []
        for sheet_name, start_line, end_line in sheet_ranges:
            section_lines = lines[start_line - 1 : end_line]
            section_metadata = dict(metadata or {})
            section_metadata.update(
                {
                    "section_title": sheet_name or section_metadata.get("section_title", ""),
                    "chunk_type": "spreadsheet_sheet",
                }
            )
            chunks.extend(
                self._chunk_lines(
                    section_lines,
                    start_line=start_line,
                    metadata=section_metadata,
                )
            )

        return chunks

    def _split_long_line(self, line: str, max_chars: int) -> List[str]:
        """Split a single long line into multiple chunks."""
        chunks = []
        for index in range(0, len(line), max_chars):
            chunks.append(line[index:index + max_chars])
        return chunks

    def _get_overlap_lines(self, lines: List[str], target_chars: int) -> List[str]:
        """Get last few lines that fit within target_chars for overlap."""
        overlap = []
        chars = 0

        for line in reversed(lines):
            line_chars = len(line)
            if chars + line_chars > target_chars:
                break
            overlap.insert(0, line)
            chars += line_chars

        return overlap
