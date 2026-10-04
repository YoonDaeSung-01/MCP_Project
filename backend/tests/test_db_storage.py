"""DB 연결, 마이그레이션 및 멱등성(Idempotency) 단위 테스트."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.services.idempotency import execute_with_idempotency
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_app.sqlite"


def test_open_connection_pragmas(temp_db: Path) -> None:
    conn = open_connection(temp_db)
    try:
        # foreign_keys 확인
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert fk == 1

        # journal_mode 확인
        jm = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert jm.lower() == "wal"

        # busy_timeout 확인
        bt = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert bt == 5000
    finally:
        conn.close()


def test_apply_migrations(temp_db: Path) -> None:
    conn = open_connection(temp_db)
    try:
        version = apply_migrations(conn)
        assert version >= 1

        # 테이블 생성 확인
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('pages', 'tasks', 'sessions', 'turns', 'mutation_logs');"
        )
        tables = {row[0] for row in cursor.fetchall()}
        assert tables == {"pages", "tasks", "sessions", "turns", "mutation_logs"}

        # 중복 적용 시 변화 없음
        second_version = apply_migrations(conn)
        assert second_version == version
    finally:
        conn.close()


def test_idempotency_retry_and_conflict(temp_db: Path) -> None:
    conn = open_connection(temp_db)
    apply_migrations(conn)
    try:
        counter = {"runs": 0}

        def _action():
            counter["runs"] += 1
            return {"result": "success", "run": counter["runs"]}

        payload = {"data": "foo", "number": 42}
        request_id = "req-12345"

        # 1. 첫 실행
        with conn:
            res1 = execute_with_idempotency(conn, request_id, payload, _action)
        assert res1["result"] == "success"
        assert counter["runs"] == 1

        # 2. 동일한 payload로 재시도 -> action 재실행 없이 기존 결과 반환
        with conn:
            res2 = execute_with_idempotency(conn, request_id, payload, _action)
        assert res2["result"] == "success"
        assert counter["runs"] == 1  # 실행 횟수 그대로

        # 3. 다른 payload로 같은 request_id 사용 -> validation_error
        different_payload = {"data": "bar", "number": 99}
        with pytest.raises(WikiError) as excinfo:
            with conn:
                execute_with_idempotency(conn, request_id, different_payload, _action)
        assert excinfo.value.code is WikiErrorCode.VALIDATION_ERROR
    finally:
        conn.close()
