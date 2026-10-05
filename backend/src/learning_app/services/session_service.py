"""Session Service.

대화 세션(Session) 및 턴(Turn)을 SQLite에 저장하고 조회한다.
ARCHITECTURE.md §5, §9 준수:
- 활성 Context(active_context) 관리
- Multi-turn 대화 기록 보존
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from learning_app.db.connection import transaction
from learning_app.db.models import (
    SessionCreate,
    SessionDTO,
    TurnCreate,
    TurnDTO,
)
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


class SessionService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create_session(self, data: SessionCreate) -> SessionDTO:
        """새로운 대화 Session을 생성한다."""
        session_id = str(uuid.uuid4())
        now_str = datetime.now(UTC).isoformat()
        ctx_json = json.dumps(data.active_context, ensure_ascii=False)

        with transaction(self._conn):
            self._conn.execute(
                """
                INSERT INTO sessions (session_id, title, active_context, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (session_id, data.title, ctx_json, now_str, now_str),
            )
        return SessionDTO(
            session_id=session_id,
            title=data.title,
            active_context=data.active_context,
            turns=[],
            created_at=now_str,
            updated_at=now_str,
        )

    def get_session(self, session_id: str, include_turns: bool = True) -> SessionDTO:
        """Session 단건 조회."""
        cursor = self._conn.execute(
            "SELECT session_id, title, active_context, created_at, updated_at FROM sessions WHERE session_id = ?;",
            (session_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise WikiError(WikiErrorCode.NOT_FOUND, f"Session을 찾을 수 없다: {session_id}")

        turns = self.list_turns(session_id) if include_turns else []
        return SessionDTO(
            session_id=row["session_id"],
            title=row["title"],
            active_context=json.loads(row["active_context"]),
            turns=turns,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_sessions(self, limit: int = 50, offset: int = 0) -> list[SessionDTO]:
        """Session 목록 조회 (턴 목록 제외)."""
        cursor = self._conn.execute(
            "SELECT session_id, title, active_context, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?;",
            (limit, offset),
        )
        return [
            SessionDTO(
                session_id=row["session_id"],
                title=row["title"],
                active_context=json.loads(row["active_context"]),
                turns=[],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in cursor.fetchall()
        ]

    def update_active_context(self, session_id: str, active_context: dict[str, Any]) -> SessionDTO:
        """Session의 활성 Context를 갱신한다."""
        now_str = datetime.now(UTC).isoformat()
        ctx_json = json.dumps(active_context, ensure_ascii=False)

        with transaction(self._conn):
            cursor = self._conn.execute(
                "UPDATE sessions SET active_context = ?, updated_at = ? WHERE session_id = ?;",
                (ctx_json, now_str, session_id),
            )
            if cursor.rowcount == 0:
                raise WikiError(WikiErrorCode.NOT_FOUND, f"Session을 찾을 수 없다: {session_id}")
        return self.get_session(session_id, include_turns=False)

    def add_turn(self, session_id: str, data: TurnCreate) -> TurnDTO:
        """Session에 새로운 대화 Turn을 추가한다."""
        # Session 존재 검증
        self.get_session(session_id, include_turns=False)

        turn_id = str(uuid.uuid4())
        now_str = datetime.now(UTC).isoformat()
        tool_calls_json = json.dumps(data.tool_calls, ensure_ascii=False) if data.tool_calls else None

        with transaction(self._conn):
            self._conn.execute(
                """
                INSERT INTO turns (turn_id, session_id, role, content, status, tool_calls, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (turn_id, session_id, data.role, data.content, data.status, tool_calls_json, now_str),
            )
            # Session의 updated_at 갱신
            self._conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?;",
                (now_str, session_id),
            )

        return TurnDTO(
            turn_id=turn_id,
            session_id=session_id,
            role=data.role,
            content=data.content,
            status=data.status,
            tool_calls=data.tool_calls,
            created_at=now_str,
        )

    def list_turns(self, session_id: str) -> list[TurnDTO]:
        """Session의 전체 대화 Turn 목록을 시간순으로 조회한다."""
        cursor = self._conn.execute(
            "SELECT turn_id, session_id, role, content, status, tool_calls, created_at FROM turns WHERE session_id = ? ORDER BY created_at ASC;",
            (session_id,),
        )
        return [
            TurnDTO(
                turn_id=row["turn_id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                status=row["status"],
                tool_calls=json.loads(row["tool_calls"]) if row["tool_calls"] else None,
                created_at=row["created_at"],
            )
            for row in cursor.fetchall()
        ]

    def delete_session(self, session_id: str) -> None:
        """Session을 삭제한다 (외래키 제약으로 하위 Turn 자동 삭제)."""
        with transaction(self._conn):
            cursor = self._conn.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))
            if cursor.rowcount == 0:
                raise WikiError(WikiErrorCode.NOT_FOUND, f"삭제할 Session이 없다: {session_id}")
