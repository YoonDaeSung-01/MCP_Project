"""SQLite Schema Migration 관리자.

migrations 디렉터리의 SQL 파일들을 읽어 순차적으로 적용하고 schema_version을 관리한다.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def apply_migrations(conn: sqlite3.Connection) -> int:
    """미적용 마이그레이션을 순차적으로 적용하고 최종 스키마 버전을 반환한다."""
    # schema_version 테이블 준비
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )
    conn.commit()

    # 현재 적용된 최대 버전 확인
    cursor = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version;")
    current_version = cursor.fetchone()[0]

    # 마이그레이션 파일 목록 수집 (예: 001_initial_schema.sql)
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    applied_count = 0
    for sql_file in sql_files:
        try:
            version = int(sql_file.name.split("_")[0])
        except (ValueError, IndexError):
            continue

        if version > current_version:
            logger.info("Applying migration %s (version %d)...", sql_file.name, version)
            sql_content = sql_file.read_text(encoding="utf-8")
            
            with conn:
                conn.executescript(sql_content)
                now_str = datetime.now(UTC).isoformat()
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?);",
                    (version, now_str),
                )
            applied_count += 1
            current_version = version

    if applied_count > 0:
        logger.info("Applied %d migrations. Current version: %d", applied_count, current_version)
    return current_version
