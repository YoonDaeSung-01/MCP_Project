"""Page Service.

사용자 노트 및 Coding Record를 SQLite에 저장하고 조회한다.
ARCHITECTURE.md §5 준수:
- expected_revision 검증 및 충돌(conflict) 처리
- request_id 멱등성 처리
- Block JSON 및 Metadata 원본 보존
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from learning_app.db.models import PageCreate, PageDTO, PageUpdate
from learning_app.services.idempotency import execute_with_idempotency
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


class PageService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create_page(self, data: PageCreate) -> PageDTO:
        """새로운 Page를 생성한다."""
        page_id = str(uuid.uuid4())
        payload = data.model_dump()

        def _execute() -> dict[str, Any]:
            now_str = datetime.now(UTC).isoformat()
            blocks_json = json.dumps(data.blocks, ensure_ascii=False)
            metadata_json = json.dumps(data.metadata, ensure_ascii=False)
            self._conn.execute(
                """
                INSERT INTO pages (page_id, kind, title, blocks, metadata, revision, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?);
                """,
                (page_id, data.kind, data.title, blocks_json, metadata_json, now_str, now_str),
            )
            return {
                "page_id": page_id,
                "kind": data.kind,
                "title": data.title,
                "blocks": data.blocks,
                "metadata": data.metadata,
                "revision": 1,
                "created_at": now_str,
                "updated_at": now_str,
            }

        with self._conn:
            res = execute_with_idempotency(self._conn, data.request_id, payload, _execute)
        return PageDTO.model_validate(res)

    def get_page(self, page_id: str) -> PageDTO:
        """Page 단건 조회."""
        cursor = self._conn.execute(
            "SELECT page_id, kind, title, blocks, metadata, revision, created_at, updated_at FROM pages WHERE page_id = ?;",
            (page_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise WikiError(WikiErrorCode.NOT_FOUND, f"Page를 찾을 수 없다: {page_id}")
        return self._row_to_dto(row)

    def list_pages(self, kind: str | None = None, limit: int = 50, offset: int = 0) -> list[PageDTO]:
        """Page 목록 조회."""
        if kind:
            cursor = self._conn.execute(
                "SELECT page_id, kind, title, blocks, metadata, revision, created_at, updated_at FROM pages WHERE kind = ? ORDER BY updated_at DESC LIMIT ? OFFSET ?;",
                (kind, limit, offset),
            )
        else:
            cursor = self._conn.execute(
                "SELECT page_id, kind, title, blocks, metadata, revision, created_at, updated_at FROM pages ORDER BY updated_at DESC LIMIT ? OFFSET ?;",
                (limit, offset),
            )
        return [self._row_to_dto(row) for row in cursor.fetchall()]

    def update_page(self, page_id: str, data: PageUpdate) -> PageDTO:
        """Page를 수정한다 (expected_revision 검증)."""
        payload = {"page_id": page_id, **data.model_dump()}

        def _execute() -> dict[str, Any]:
            cursor = self._conn.execute(
                "SELECT page_id, kind, title, blocks, metadata, revision, created_at FROM pages WHERE page_id = ?;",
                (page_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise WikiError(WikiErrorCode.NOT_FOUND, f"Page를 찾을 수 없다: {page_id}")

            current_revision = row["revision"]
            if current_revision != data.expected_revision:
                raise WikiError(
                    WikiErrorCode.SOURCE_CHANGED,
                    f"다른 변경이 먼저 반영되었다 (현재 revision: {current_revision}, 요청 revision: {data.expected_revision})",
                )

            new_title = data.title if data.title is not None else row["title"]
            new_blocks = data.blocks if data.blocks is not None else json.loads(row["blocks"])
            new_meta = data.metadata if data.metadata is not None else json.loads(row["metadata"])
            new_revision = current_revision + 1
            now_str = datetime.now(UTC).isoformat()

            self._conn.execute(
                """
                UPDATE pages
                SET title = ?, blocks = ?, metadata = ?, revision = ?, updated_at = ?
                WHERE page_id = ?;
                """,
                (
                    new_title,
                    json.dumps(new_blocks, ensure_ascii=False),
                    json.dumps(new_meta, ensure_ascii=False),
                    new_revision,
                    now_str,
                    page_id,
                ),
            )
            return {
                "page_id": page_id,
                "kind": row["kind"],
                "title": new_title,
                "blocks": new_blocks,
                "metadata": new_meta,
                "revision": new_revision,
                "created_at": row["created_at"],
                "updated_at": now_str,
            }

        with self._conn:
            res = execute_with_idempotency(self._conn, data.request_id, payload, _execute)
        return PageDTO.model_validate(res)

    def delete_page(self, page_id: str) -> None:
        """Page를 삭제한다."""
        with self._conn:
            cursor = self._conn.execute("DELETE FROM pages WHERE page_id = ?;", (page_id,))
            if cursor.rowcount == 0:
                raise WikiError(WikiErrorCode.NOT_FOUND, f"삭제할 Page가 없다: {page_id}")

    @staticmethod
    def _row_to_dto(row: sqlite3.Row) -> PageDTO:
        return PageDTO(
            page_id=row["page_id"],
            kind=row["kind"],
            title=row["title"],
            blocks=json.loads(row["blocks"]),
            metadata=json.loads(row["metadata"]),
            revision=row["revision"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
