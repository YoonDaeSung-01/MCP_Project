"""Backup & Restore Service.

ARCHITECTURE.md §10, §13 준수:
- SQLite Backup API(conn.backup)를 통한 온라인 원자적 스냅샷 생성
- Restore 전 Schema 및 파일 무결성 사전 검증 (PRAGMA integrity_check, schema_version 확인)
- 검증 실패 시 기존 Database 보존
"""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from learning_app.db.connection import open_connection
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode

logger = logging.getLogger(__name__)

BACKUP_FILENAME_PREFIX = "backup_"
BACKUP_FILENAME_SUFFIX = ".sqlite"


class BackupService:
    def __init__(self, db_path: Path, backup_dir: Path) -> None:
        self._db_path = db_path
        self._backup_dir = backup_dir
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> dict[str, Any]:
        """현재 데이터베이스의 온라인 백업 스냅샷을 생성한다."""
        if str(self._db_path) == ":memory:":
            raise WikiError(WikiErrorCode.VALIDATION_ERROR, "메모리 DB는 파일 백업을 생성할 수 없다")

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_file = self._backup_dir / f"{BACKUP_FILENAME_PREFIX}{timestamp}{BACKUP_FILENAME_SUFFIX}"

        source_conn = open_connection(self._db_path)
        try:
            target_conn = sqlite3.connect(str(backup_file))
            try:
                # SQLite Online Backup API
                source_conn.backup(target_conn)
            finally:
                target_conn.close()
        finally:
            source_conn.close()

        file_stat = backup_file.stat()
        logger.info("Created backup file %s (%d bytes)", backup_file.name, file_stat.st_size)
        return {
            "filename": backup_file.name,
            "filepath": str(backup_file),
            "size_bytes": file_stat.st_size,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def list_backups(self) -> list[dict[str, Any]]:
        """존재하는 백업 파일 목록을 반환한다."""
        files = sorted(
            self._backup_dir.glob(f"{BACKUP_FILENAME_PREFIX}*{BACKUP_FILENAME_SUFFIX}"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        return [
            {
                "filename": f.name,
                "filepath": str(f),
                "size_bytes": f.stat().st_size,
                "created_at": datetime.fromtimestamp(f.stat().st_mtime, UTC).isoformat(),
            }
            for f in files
        ]

    def verify_backup_file(self, backup_file: Path) -> None:
        """백업 파일의 무결성과 필수 스키마를 검증한다. 이상 시 WikiError 발생."""
        if not backup_file.exists() or not backup_file.is_file():
            raise WikiError(WikiErrorCode.NOT_FOUND, f"백업 파일을 찾을 수 없다: {backup_file.name}")

        try:
            conn = sqlite3.connect(str(backup_file))
            try:
                # 1. 파일 무결성 검사
                cursor = conn.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                if result is None or result[0] != "ok":
                    raise WikiError(
                        WikiErrorCode.VALIDATION_ERROR,
                        f"백업 파일의 무결성 검증 실패: {result[0] if result else 'unknown'}",
                    )

                # 2. 필수 테이블 존재 확인
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('schema_version', 'pages', 'tasks', 'sessions');"
                )
                tables = {row[0] for row in cursor.fetchall()}
                required = {"schema_version", "pages", "tasks", "sessions"}
                if not required.issubset(tables):
                    missing = required - tables
                    raise WikiError(
                        WikiErrorCode.VALIDATION_ERROR,
                        f"백업 파일에 필수 테이블이 누락되었다: {missing}",
                    )
            finally:
                conn.close()
        except sqlite3.DatabaseError as exc:
            raise WikiError(
                WikiErrorCode.VALIDATION_ERROR,
                f"백업 파일이 유효한 SQLite 데이터베이스가 아니다: {exc}",
            ) from exc

    def restore_backup(self, backup_filename: str) -> None:
        """사전 검증 후 백업 파일로부터 활성 데이터베이스를 복원한다."""
        backup_file = self._backup_dir / backup_filename
        self.verify_backup_file(backup_file)

        # 활성 DB 안전 보존 (롤백용)
        pre_restore = self._db_path.with_suffix(".pre_restore")
        has_existing = self._db_path.exists()
        if has_existing:
            shutil.copy2(self._db_path, pre_restore)

        try:
            # 복원: backup 파일을 active_db_path로 안전하게 복사
            # 또는 SQLite backup API로 덮어쓰기
            dest_conn = open_connection(self._db_path)
            try:
                src_conn = sqlite3.connect(str(backup_file))
                try:
                    src_conn.backup(dest_conn)
                finally:
                    src_conn.close()
            finally:
                dest_conn.close()

            # 복원 완료 후 롤백용 임시 파일 정리
            if pre_restore.exists():
                pre_restore.unlink(missing_ok=True)
            logger.info("Successfully restored database from %s", backup_filename)
        except Exception as exc:
            # 복원 실패 시 기존 파일 복원
            if has_existing and pre_restore.exists():
                shutil.copy2(pre_restore, self._db_path)
                pre_restore.unlink(missing_ok=True)
            logger.error("Database restore failed, rolled back to original: %s", exc)
            raise WikiError(
                WikiErrorCode.READ_ERROR,
                f"데이터베이스 복원 중 오류가 발생하여 기존 상태로 롤백했다: {exc}",
            ) from exc
