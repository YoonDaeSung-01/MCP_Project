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


def _split_sql_script(script: str) -> list[str]:
    """SQL 스크립트를 개별 실행 문장으로 분리한다.

    한 줄에 여러 문장이 있거나, 문자열 내부/주석/트리거 본문에 세미콜론이 포함된 경우도
    sqlite3.complete_statement()를 통해 정확한 문장 경계를 판별하여 분리한다.
    """
    statements: list[str] = []
    buffer = ""

    for char in script:
        buffer += char
        if char == ";":
            if sqlite3.complete_statement(buffer):
                stmt = buffer.strip()
                if stmt:
                    statements.append(stmt)
                buffer = ""

    remainder = buffer.strip()
    if remainder:
        statements.append(remainder)

    return statements


def apply_migrations(conn: sqlite3.Connection) -> int:
    """미적용 마이그레이션을 순차적으로 적용하고 최종 스키마 버전을 반환한다 (B04)."""
    # schema_version 테이블 준비
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )

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
            statements = _split_sql_script(sql_content)

            # B04: SQL 실행과 version 기록을 단일 트랜잭션으로 원자적 커밋/롤백
            conn.execute("BEGIN IMMEDIATE;")
            try:
                for stmt in statements:
                    conn.execute(stmt)
                now_str = datetime.now(UTC).isoformat()
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?);",
                    (version, now_str),
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                logger.error("Migration %s failed, rolled back completely.", sql_file.name)
                raise

            applied_count += 1
            current_version = version

    if applied_count > 0:
        logger.info("Applied %d migrations. Current version: %d", applied_count, current_version)
    return current_version
