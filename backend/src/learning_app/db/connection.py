"""SQLite 연결 및 환경 설정.

ARCHITECTURE.md §5, §13 준수:
- WAL 모드 활성화 (동시 읽기/쓰기 성능 및 안전성)
- foreign_keys = ON
- busy_timeout 설정
- Row factory 설정
- isolation_level = None 및 BEGIN IMMEDIATE 기반 transaction() 관리자로 동시성 보장 (B04)
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


def open_connection(db_path: Path | str) -> sqlite3.Connection:
    """SQLite 데이터베이스 연결을 생성하고 기본 설정을 적용한다.

    isolation_level=None(autocommit) 모드로 설정하여 암묵적 읽기 트랜잭션이
    동시 쓰기 요청 시 SQLITE_BUSY_SNAPSHOT을 유발하지 않도록 방지한다.
    """
    path = Path(db_path)
    if str(db_path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(db_path),
        timeout=10.0,
        isolation_level=None,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    if str(db_path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """BEGIN IMMEDIATE 기반의 트랜잭션 컨텍스트 매니저.

    동시 쓰기 요청 시 SQLITE_BUSY_SNAPSHOT을 방지하고 작업과 멱등성 로그의 원자성을 보장한다.
    """
    conn.execute("BEGIN IMMEDIATE;")
    try:
        yield conn
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise
