"""Task Service.

할 일(Task)을 SQLite에 저장, 상태 전이 및 복원을 관리한다.
ARCHITECTURE.md §5 준수:
- Task 상태: open, done, archived
- 보관(archived) 및 복원(restore) 지원
- expected_revision 검증 및 request_id 멱등성 처리
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from learning_app.db.models import TaskCreate, TaskDTO, TaskStatus, TaskUpdate
from learning_app.services.idempotency import execute_with_idempotency
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


class TaskService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create_task(self, data: TaskCreate) -> TaskDTO:
        """새로운 Task를 생성한다."""
        task_id = str(uuid.uuid4())
        payload = data.model_dump()

        def _execute() -> dict[str, Any]:
            now_str = datetime.now(UTC).isoformat()
            target_ref_json = json.dumps(data.target_ref, ensure_ascii=False) if data.target_ref else None
            self._conn.execute(
                """
                INSERT INTO tasks (task_id, title, status, due_date, target_ref, revision, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?);
                """,
                (task_id, data.title, TaskStatus.OPEN.value, data.due_date, target_ref_json, now_str, now_str),
            )
            return {
                "task_id": task_id,
                "title": data.title,
                "status": TaskStatus.OPEN.value,
                "due_date": data.due_date,
                "target_ref": data.target_ref,
                "revision": 1,
                "created_at": now_str,
                "updated_at": now_str,
            }

        with self._conn:
            res = execute_with_idempotency(self._conn, data.request_id, payload, _execute)
        return TaskDTO.model_validate(res)

    def get_task(self, task_id: str) -> TaskDTO:
        """Task 단건 조회."""
        cursor = self._conn.execute(
            "SELECT task_id, title, status, due_date, target_ref, revision, created_at, updated_at FROM tasks WHERE task_id = ?;",
            (task_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise WikiError(WikiErrorCode.NOT_FOUND, f"Task를 찾을 수 없다: {task_id}")
        return self._row_to_dto(row)

    def list_tasks(self, status: str | None = None, limit: int = 50, offset: int = 0) -> list[TaskDTO]:
        """Task 목록 조회."""
        if status:
            cursor = self._conn.execute(
                "SELECT task_id, title, status, due_date, target_ref, revision, created_at, updated_at FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?;",
                (status, limit, offset),
            )
        else:
            cursor = self._conn.execute(
                "SELECT task_id, title, status, due_date, target_ref, revision, created_at, updated_at FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?;",
                (limit, offset),
            )
        return [self._row_to_dto(row) for row in cursor.fetchall()]

    def update_task(self, task_id: str, data: TaskUpdate) -> TaskDTO:
        """Task를 수정한다 (expected_revision 검증)."""
        payload = {"task_id": task_id, **data.model_dump()}

        def _execute() -> dict[str, Any]:
            cursor = self._conn.execute(
                "SELECT task_id, title, status, due_date, target_ref, revision, created_at FROM tasks WHERE task_id = ?;",
                (task_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise WikiError(WikiErrorCode.NOT_FOUND, f"Task를 찾을 수 없다: {task_id}")

            current_revision = row["revision"]
            if current_revision != data.expected_revision:
                raise WikiError(
                    WikiErrorCode.SOURCE_CHANGED,
                    f"다른 변경이 먼저 반영되었다 (현재 revision: {current_revision}, 요청 revision: {data.expected_revision})",
                )

            new_title = data.title if data.title is not None else row["title"]
            new_status = data.status if data.status is not None else row["status"]
            new_due_date = data.due_date if data.due_date is not None else row["due_date"]
            new_target_ref = data.target_ref if data.target_ref is not None else (json.loads(row["target_ref"]) if row["target_ref"] else None)
            new_revision = current_revision + 1
            now_str = datetime.now(UTC).isoformat()

            self._conn.execute(
                """
                UPDATE tasks
                SET title = ?, status = ?, due_date = ?, target_ref = ?, revision = ?, updated_at = ?
                WHERE task_id = ?;
                """,
                (
                    new_title,
                    new_status,
                    new_due_date,
                    json.dumps(new_target_ref, ensure_ascii=False) if new_target_ref else None,
                    new_revision,
                    now_str,
                    task_id,
                ),
            )
            return {
                "task_id": task_id,
                "title": new_title,
                "status": new_status,
                "due_date": new_due_date,
                "target_ref": new_target_ref,
                "revision": new_revision,
                "created_at": row["created_at"],
                "updated_at": now_str,
            }

        with self._conn:
            res = execute_with_idempotency(self._conn, data.request_id, payload, _execute)
        return TaskDTO.model_validate(res)

    def archive_task(self, task_id: str, expected_revision: int, request_id: str | None = None) -> TaskDTO:
        """Task를 보관(archived) 상태로 변경한다."""
        return self.update_task(
            task_id,
            TaskUpdate(expected_revision=expected_revision, status=TaskStatus.ARCHIVED.value, request_id=request_id),
        )

    def restore_task(self, task_id: str, expected_revision: int, request_id: str | None = None) -> TaskDTO:
        """보관된 Task를 다시 열림(open) 상태로 복원한다."""
        return self.update_task(
            task_id,
            TaskUpdate(expected_revision=expected_revision, status=TaskStatus.OPEN.value, request_id=request_id),
        )

    def delete_task(self, task_id: str) -> None:
        """Task를 삭제한다."""
        with self._conn:
            cursor = self._conn.execute("DELETE FROM tasks WHERE task_id = ?;", (task_id,))
            if cursor.rowcount == 0:
                raise WikiError(WikiErrorCode.NOT_FOUND, f"삭제할 Task가 없다: {task_id}")

    @staticmethod
    def _row_to_dto(row: sqlite3.Row) -> TaskDTO:
        return TaskDTO(
            task_id=row["task_id"],
            title=row["title"],
            status=row["status"],
            due_date=row["due_date"],
            target_ref=json.loads(row["target_ref"]) if row["target_ref"] else None,
            revision=row["revision"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
