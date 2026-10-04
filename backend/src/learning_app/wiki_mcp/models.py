"""Wiki 조회 결과 Model. MCP Tool과 Backend가 같은 구조를 사용한다."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

SOURCE_TYPE_WIKI_NOTE = "wiki_note"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class SourceReference(_Frozen):
    """실제로 읽거나 찾은 원문 위치. ARCHITECTURE §7."""

    source_type: str = SOURCE_TYPE_WIKI_NOTE
    note_id: str
    section_id: str | None
    file_version: str
    start_line: int
    end_line: int


class HeadingInfo(_Frozen):
    section_id: str
    level: int
    title: str
    path: list[str]
    start_line: int
    end_line: int


class NoteSummary(_Frozen):
    note_id: str
    collection: str
    title: str
    aliases: list[str]
    tags: list[str]
    status: str | None
    file_version: str


class CollectionState(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class CollectionStatus(_Frozen):
    collection: str
    state: CollectionState
    note_count: int
    failed_count: int
    failed_examples: list[str]
    error: str | None


class IndexStatus(_Frozen):
    generation: int
    refreshed_at: datetime
    collections: list[CollectionStatus]
    complete: bool


class NoteList(_Frozen):
    items: list[NoteSummary]
    next_cursor: str | None
    index: IndexStatus


class Snippet(_Frozen):
    heading_path: list[str]
    text: str
    source_reference: SourceReference


class SearchHit(_Frozen):
    rank: int
    note_id: str
    collection: str
    title: str
    matched_in: str
    snippets: list[Snippet]


class SearchResult(_Frozen):
    query: str
    hits: list[SearchHit]
    total_matches: int
    applied_limit: int
    index: IndexStatus
    complete: bool
    warnings: list[str]


class HeadingsResult(_Frozen):
    note_id: str
    title: str
    file_version: str
    total_lines: int
    headings: list[HeadingInfo]
    warnings: list[str]


class NoteContent(_Frozen):
    note_id: str
    title: str
    file_version: str
    section: HeadingInfo | None
    content: str
    start_line: int
    end_line: int
    total_lines: int
    next_cursor: str | None
    source_reference: SourceReference
    warnings: list[str]
