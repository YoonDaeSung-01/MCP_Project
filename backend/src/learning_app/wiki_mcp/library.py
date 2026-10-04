"""Wiki 조회 Library. Index(목록과 검색)와 실시간 읽기(Heading과 본문)를 제공한다.

MCP Protocol을 모른다. Step 2.2의 MCP Server가 이 Library를 Tool로 노출한다.
- 목록과 검색은 Memory Index를 사용한다. Index는 시작과 refresh 때 갱신한다.
- Heading과 본문 읽기는 매번 File을 읽어 현재 file_version을 확인한다.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import IntEnum
from pathlib import Path

from learning_app.wiki_mcp.config import (
    NOTE_SUFFIX,
    Collection,
    CollectionSpec,
    WikiLimits,
)
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode
from learning_app.wiki_mcp.models import (
    CollectionState,
    CollectionStatus,
    HeadingInfo,
    HeadingsResult,
    IndexStatus,
    NoteContent,
    NoteList,
    NoteSummary,
    SearchHit,
    SearchResult,
    Snippet,
    SourceReference,
)
from learning_app.wiki_mcp.parser import (
    SECTION_ID_PREFIX,
    Heading,
    ParsedNote,
    normalize_text,
    parse_note,
    split_lines,
)
from learning_app.wiki_mcp.paths import (
    is_excluded_name,
    make_note_id,
    parse_note_id,
    read_source,
    resolve_note_file,
)

MAX_FAILED_EXAMPLES = 5
CURSOR_SEPARATOR = "."
ELLIPSIS = "…"


class MatchTier(IntEnum):
    """검색 일치 위치. 값이 클수록 높은 순위다. 제목과 Alias가 본문보다 우선한다."""

    BODY = 1
    TAG = 2
    ALIAS = 3
    TITLE = 4
    ALIAS_EXACT = 5
    TITLE_EXACT = 6


@dataclass(frozen=True)
class _IndexedNote:
    note_id: str
    collection: Collection
    summary: NoteSummary
    lines: tuple[str, ...]
    norm_lines: tuple[str, ...]
    body_start: int
    headings: tuple[Heading, ...]
    title_norm: str
    aliases_norm: tuple[str, ...]
    tags_norm: tuple[str, ...]


@dataclass(frozen=True)
class _LoadedNote:
    note_id: str
    version: str
    lines: list[str]
    parsed: ParsedNote


class WikiLibrary:
    def __init__(self, specs: dict[Collection, CollectionSpec], limits: WikiLimits) -> None:
        self._specs = specs
        self._limits = limits
        self._notes: dict[str, _IndexedNote] = {}
        self._statuses: dict[Collection, CollectionStatus] = {}
        self._generation = 0
        self._refreshed_at = datetime.now(UTC)

    # ------------------------------------------------------------------ Index

    def refresh(self) -> IndexStatus:
        """모든 Collection을 다시 읽어 Index를 교체한다."""
        notes: dict[str, _IndexedNote] = {}
        statuses: dict[Collection, CollectionStatus] = {}
        for collection, spec in self._specs.items():
            found, status = self._scan_collection(spec)
            notes.update({note.note_id: note for note in found})
            statuses[collection] = status
        self._notes = notes
        self._statuses = statuses
        self._generation += 1
        self._refreshed_at = datetime.now(UTC)
        return self._index_status(list(self._specs))

    def _scan_collection(self, spec: CollectionSpec) -> tuple[list[_IndexedNote], CollectionStatus]:
        name = spec.collection.value
        if spec.root is None:
            return [], _status(name, CollectionState.UNAVAILABLE, 0, 0, [], "Root가 설정되지 않았다")
        try:
            root = spec.root.resolve(strict=True)
        except OSError:
            return [], _status(name, CollectionState.UNAVAILABLE, 0, 0, [], "Root를 열 수 없다")
        if not root.is_dir():
            return [], _status(name, CollectionState.UNAVAILABLE, 0, 0, [], "Root가 Directory가 아니다")

        files: list[tuple[str, ...]] = []
        failed: list[str] = []
        _walk(root, (), spec, files, failed)

        notes: list[_IndexedNote] = []
        for parts in files:
            note_id = make_note_id(spec.collection, parts)
            try:
                path = resolve_note_file(spec, parts)
                text, version = read_source(path, note_id, self._limits.max_file_bytes)
            except WikiError:
                failed.append(note_id)
                continue
            notes.append(_build_indexed(spec.collection, note_id, parts, text, version))

        if spec.includes is not None and not files and not failed:
            return [], _status(name, CollectionState.UNAVAILABLE, 0, 0, [], "포함 대상 경로를 찾을 수 없다")
        if failed and not notes:
            state = CollectionState.UNAVAILABLE
        elif failed:
            state = CollectionState.PARTIAL
        else:
            state = CollectionState.OK
        return notes, _status(name, state, len(notes), len(failed), failed[:MAX_FAILED_EXAMPLES], None)

    def _index_status(self, selected: list[Collection]) -> IndexStatus:
        statuses = [self._statuses[c] for c in selected if c in self._statuses]
        return IndexStatus(
            generation=self._generation,
            refreshed_at=self._refreshed_at,
            collections=statuses,
            complete=all(s.state is CollectionState.OK for s in statuses) and bool(statuses),
        )

    def index_status(self) -> IndexStatus:
        return self._index_status(list(self._specs))

    # ------------------------------------------------------------------ 목록

    def list_notes(
        self, collection: str | None = None, cursor: str | None = None, limit: int | None = None
    ) -> NoteList:
        selected = self._select(collection)
        applied = self._apply_limit(limit)
        notes = sorted(
            (n for n in self._notes.values() if n.collection in selected),
            key=lambda n: n.note_id,
        )
        offset = self._parse_index_cursor(cursor)
        page = notes[offset : offset + applied]
        next_offset = offset + applied
        return NoteList(
            items=[n.summary for n in page],
            next_cursor=(
                f"{self._generation}{CURSOR_SEPARATOR}{next_offset}"
                if next_offset < len(notes)
                else None
            ),
            index=self._index_status(selected),
        )

    # ------------------------------------------------------------------ 검색

    def search_notes(
        self, query: str, collection: str | None = None, limit: int | None = None
    ) -> SearchResult:
        selected = self._select(collection)
        applied = self._apply_limit(limit)
        terms = normalize_text(query).split()
        if not terms:
            raise WikiError(WikiErrorCode.VALIDATION_ERROR, "query가 비어 있다")
        query_norm = " ".join(terms)

        matches: list[tuple[MatchTier, _IndexedNote]] = []
        for note in self._notes.values():
            if note.collection not in selected:
                continue
            tier = _match_tier(note, terms, query_norm)
            if tier is not None:
                matches.append((tier, note))
        matches.sort(key=lambda m: (-int(m[0]), m[1].note_id))

        hits = [
            SearchHit(
                rank=position,
                note_id=note.note_id,
                collection=note.collection.value,
                title=note.summary.title,
                matched_in=tier.name.lower(),
                snippets=self._snippets(note, terms),
            )
            for position, (tier, note) in enumerate(matches[:applied], start=1)
        ]
        index = self._index_status(selected)
        warnings = [
            f"{s.collection}: {s.state.value}" + (f" ({s.error})" if s.error else "")
            for s in index.collections
            if s.state is not CollectionState.OK
        ]
        if warnings:
            warnings.insert(0, "일부 Collection의 검색 범위가 누락되었다. 결과 없음은 전체에 없다는 뜻이 아니다")
        return SearchResult(
            query=query,
            hits=hits,
            total_matches=len(matches),
            applied_limit=applied,
            index=index,
            complete=index.complete,
            warnings=warnings,
        )

    def _snippets(self, note: _IndexedNote, terms: list[str]) -> list[Snippet]:
        scored: list[tuple[int, int]] = []
        for position in range(note.body_start, len(note.norm_lines)):
            count = sum(1 for term in terms if term in note.norm_lines[position])
            if count:
                scored.append((-count, position))
        scored.sort()
        chosen = sorted(position for _, position in scored[: self._limits.snippets_per_note])
        snippets: list[Snippet] = []
        for position in chosen:
            line_number = position + 1
            section = _section_for_line(note.headings, line_number)
            text = note.lines[position].strip()
            if len(text) > self._limits.snippet_max_chars:
                text = text[: self._limits.snippet_max_chars - len(ELLIPSIS)] + ELLIPSIS
            snippets.append(
                Snippet(
                    heading_path=list(section.path) if section else [],
                    text=text,
                    source_reference=SourceReference(
                        note_id=note.note_id,
                        section_id=section.section_id if section else None,
                        file_version=note.summary.file_version,
                        start_line=line_number,
                        end_line=line_number,
                    ),
                )
            )
        return snippets

    # ------------------------------------------------------------------ 읽기

    def get_headings(self, note_id: str) -> HeadingsResult:
        loaded = self._load(note_id)
        return HeadingsResult(
            note_id=note_id,
            title=loaded.parsed.title,
            file_version=loaded.version,
            total_lines=len(loaded.lines),
            headings=[_heading_info(h) for h in loaded.parsed.headings],
            warnings=list(loaded.parsed.warnings),
        )

    def read_note(
        self,
        note_id: str,
        section_id: str | None = None,
        file_version: str | None = None,
        cursor: str | None = None,
    ) -> NoteContent:
        loaded = self._load(note_id)
        if file_version is not None and file_version != loaded.version:
            raise WikiError(
                WikiErrorCode.SOURCE_CHANGED,
                "File이 바뀌었다. get_headings로 목차를 다시 조회한다",
            )
        offset = 0
        if cursor is not None:
            cursor_version, offset = _parse_read_cursor(cursor)
            if cursor_version != loaded.version:
                raise WikiError(
                    WikiErrorCode.SOURCE_CHANGED,
                    "File이 바뀌어 cursor가 무효다. 처음부터 다시 읽는다",
                )

        section: Heading | None = None
        first, last = 1, len(loaded.lines)
        if section_id is not None:
            section = next((h for h in loaded.parsed.headings if h.section_id == section_id), None)
            if section is None:
                if not re.fullmatch(rf"{SECTION_ID_PREFIX}\d+", section_id):
                    raise WikiError(WikiErrorCode.VALIDATION_ERROR, "section_id 형식이 올바르지 않다")
                raise WikiError(WikiErrorCode.NOT_FOUND, f"Section을 찾을 수 없다: {section_id}")
            first, last = section.start_line, section.end_line

        text = "\n".join(loaded.lines[first - 1 : last])
        if offset > len(text):
            raise WikiError(WikiErrorCode.VALIDATION_ERROR, "cursor 위치가 범위를 벗어났다")
        end = min(offset + self._limits.read_max_chars, len(text))
        if end < len(text):
            newline = text.rfind("\n", offset, end)
            if newline > offset:
                end = newline + 1
        chunk = text[offset:end]
        chunk_first = first + text.count("\n", 0, offset)
        chunk_last = chunk_first + chunk.rstrip("\n").count("\n")
        return NoteContent(
            note_id=note_id,
            title=loaded.parsed.title,
            file_version=loaded.version,
            section=_heading_info(section) if section else None,
            content=chunk,
            start_line=chunk_first,
            end_line=chunk_last,
            total_lines=len(loaded.lines),
            next_cursor=(
                f"{loaded.version}{CURSOR_SEPARATOR}{end}" if end < len(text) else None
            ),
            source_reference=SourceReference(
                note_id=note_id,
                section_id=section.section_id if section else None,
                file_version=loaded.version,
                start_line=chunk_first,
                end_line=chunk_last,
            ),
            warnings=list(loaded.parsed.warnings),
        )

    def _load(self, note_id: str) -> _LoadedNote:
        collection, parts = parse_note_id(note_id)
        path = resolve_note_file(self._specs[collection], parts)
        text, version = read_source(path, note_id, self._limits.max_file_bytes)
        lines = split_lines(text)
        parsed = parse_note(lines, fallback_title=Path(parts[-1]).stem)
        return _LoadedNote(note_id=note_id, version=version, lines=lines, parsed=parsed)

    # ------------------------------------------------------------------ 공통

    def _select(self, collection: str | None) -> list[Collection]:
        if collection is None:
            return list(self._specs)
        try:
            return [Collection(collection)]
        except ValueError:
            raise WikiError(
                WikiErrorCode.VALIDATION_ERROR, f"알 수 없는 collection이다: {collection}"
            ) from None

    def _apply_limit(self, limit: int | None) -> int:
        """limit이 없으면 기본값, 최대값 초과면 최대값을 쓴다. 적용 값은 결과에 포함한다."""
        if limit is None:
            return self._limits.default_limit
        if limit < 1:
            raise WikiError(WikiErrorCode.VALIDATION_ERROR, "limit은 1 이상이어야 한다")
        return min(limit, self._limits.max_limit)

    def _parse_index_cursor(self, cursor: str | None) -> int:
        if cursor is None:
            return 0
        generation, separator, offset = cursor.partition(CURSOR_SEPARATOR)
        if not (separator and generation.isdigit() and offset.isdigit()):
            raise WikiError(WikiErrorCode.VALIDATION_ERROR, "cursor 형식이 올바르지 않다")
        if int(generation) != self._generation:
            raise WikiError(
                WikiErrorCode.SOURCE_CHANGED, "Index가 갱신되어 cursor가 무효다. 처음부터 다시 조회한다"
            )
        return int(offset)


def _parse_read_cursor(cursor: str) -> tuple[str, int]:
    version, separator, offset = cursor.partition(CURSOR_SEPARATOR)
    if not (separator and version and offset.isdigit()):
        raise WikiError(WikiErrorCode.VALIDATION_ERROR, "cursor 형식이 올바르지 않다")
    return version, int(offset)


def _status(
    name: str,
    state: CollectionState,
    count: int,
    failed_count: int,
    examples: list[str],
    error: str | None,
) -> CollectionStatus:
    return CollectionStatus(
        collection=name,
        state=state,
        note_count=count,
        failed_count=failed_count,
        failed_examples=examples,
        error=error,
    )


def _walk(
    directory: Path,
    parts: tuple[str, ...],
    spec: CollectionSpec,
    files: list[tuple[str, ...]],
    failed: list[str],
) -> None:
    """제외 이름, Symlink와 Junction을 건너뛰며 Note File을 모은다."""
    try:
        with os.scandir(directory) as iterator:
            entries = sorted(iterator, key=lambda e: e.name)
    except OSError:
        failed.append("/".join(parts) + "/" if parts else "./")
        return
    for entry in entries:
        if is_excluded_name(entry.name):
            continue
        if not parts and spec.includes is not None and entry.name not in spec.includes:
            continue
        if entry.is_symlink() or entry.is_junction():
            continue
        child = (*parts, entry.name)
        if entry.is_dir(follow_symlinks=False):
            _walk(Path(entry.path), child, spec, files, failed)
        elif entry.is_file(follow_symlinks=False) and entry.name.casefold().endswith(NOTE_SUFFIX):
            files.append(child)


def _build_indexed(
    collection: Collection, note_id: str, parts: tuple[str, ...], text: str, version: str
) -> _IndexedNote:
    lines = split_lines(text)
    parsed = parse_note(lines, fallback_title=Path(parts[-1]).stem)
    return _IndexedNote(
        note_id=note_id,
        collection=collection,
        summary=NoteSummary(
            note_id=note_id,
            collection=collection.value,
            title=parsed.title,
            aliases=list(parsed.aliases),
            tags=list(parsed.tags),
            status=parsed.status,
            file_version=version,
        ),
        lines=tuple(lines),
        norm_lines=tuple(normalize_text(line) for line in lines),
        body_start=parsed.body_start,
        headings=parsed.headings,
        title_norm=normalize_text(parsed.title),
        aliases_norm=tuple(normalize_text(a) for a in parsed.aliases),
        tags_norm=tuple(normalize_text(t) for t in parsed.tags),
    )


def _match_tier(note: _IndexedNote, terms: list[str], query_norm: str) -> MatchTier | None:
    """모든 검색어가 포함되어야 일치한다. 가장 높은 순위의 위치를 반환한다."""
    if note.title_norm == query_norm:
        return MatchTier.TITLE_EXACT
    if query_norm in note.aliases_norm:
        return MatchTier.ALIAS_EXACT
    if all(t in note.title_norm for t in terms):
        return MatchTier.TITLE
    if any(all(t in alias for t in terms) for alias in note.aliases_norm):
        return MatchTier.ALIAS
    if all(any(t in tag for tag in note.tags_norm) for t in terms):
        return MatchTier.TAG
    body = note.norm_lines[note.body_start :]
    for term in terms:
        found = (
            term in note.title_norm
            or any(term in alias for alias in note.aliases_norm)
            or any(term in tag for tag in note.tags_norm)
            or any(term in line for line in body)
        )
        if not found:
            return None
    return MatchTier.BODY


def _section_for_line(headings: tuple[Heading, ...], line: int) -> Heading | None:
    """줄을 포함하는 가장 깊은 Section을 반환한다. 첫 Heading 앞의 줄은 None이다."""
    found: Heading | None = None
    for heading in headings:
        if heading.start_line <= line <= heading.end_line:
            found = heading
    return found


def _heading_info(heading: Heading) -> HeadingInfo:
    return HeadingInfo(
        section_id=heading.section_id,
        level=heading.level,
        title=heading.title,
        path=list(heading.path),
        start_line=heading.start_line,
        end_line=heading.end_line,
    )
