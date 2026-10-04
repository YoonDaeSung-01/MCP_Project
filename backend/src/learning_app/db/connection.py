"""SQLite 연결 및 환경 설정.

ARCHITECTURE.md §5, §13 준수:
- WAL 모드 활성화 (동시 읽기/쓰기 성능 및 안전성)
- foreign_keys = ON
- busy_timeout 설정
- Row factory 설정
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def open_connection(db_path: Path | str) -> sqlite3.Connection:
    """SQLite 데이터베이스 연결을 생성하고 기본 설정을 적용한다."""
    path = Path(db_path)
    if str(db_path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    # autocommit=True 상태에서 PRAGMA를 적용한 뒤 autocommit=False로 전환 (WAL 모드 전환 시 트랜잭션 충돌 방지)
    conn = sqlite3.connect(
        str(db_path),
        timeout=10.0,
        autocommit=True,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    if str(db_path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")

    conn.autocommit = False
    return conn
