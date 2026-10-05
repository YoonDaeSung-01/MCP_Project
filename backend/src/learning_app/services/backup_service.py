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


SUPPORTED_SCHEMA_VERSIONS: set[int] = {1}
REQUIRED_TABLE_COLUMNS: dict[str, set[str]] = {
    "schema_version": {"version", "applied_at"},
    "pages": {"page_id", "kind", "title", "blocks", "metadata", "revision", "created_at", "updated_at"},
    "tasks": {"task_id", "title", "status", "due_date", "target_ref", "revision", "created_at", "updated_at"},
    "sessions": {"session_id", "title", "active_context", "created_at", "updated_at"},
    "turns": {"turn_id", "session_id", "role", "content", "status", "tool_calls", "created_at"},
    "mutation_logs": {"request_id", "payload_hash", "response_json", "created_at"},
}
REQUIRED_FOREIGN_KEYS: dict[str, list[dict[str, str]]] = {
    "turns": [
        {"table": "sessions", "from": "session_id", "to": "session_id"},
    ],
}


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
        # 동일 초 생성 시 파일 덮어쓰기 방지
        seq = 1
        while backup_file.exists():
            backup_file = self._backup_dir / f"{BACKUP_FILENAME_PREFIX}{timestamp}_{seq}{BACKUP_FILENAME_SUFFIX}"
            seq += 1

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
        """백업 파일의 무결성과 필수 스키마를 검증한다. 이상 시 WikiError 발생 (B02).

        ARCHITECTURE.md §13, PRD FR-20 준수:
        - SQLite 파일 무결성(PRAGMA integrity_check) 검사
        - 외래 키 제약 조건 및 데이터 관계(PRAGMA foreign_key_check) 검사
        - 지원하는 스키마 버전 유효성 검사
        - 필수 테이블 및 각 테이블의 필수 컬럼 존재 여부 검사
        """
        if not backup_file.exists() or not backup_file.is_file():
            raise WikiError(WikiErrorCode.NOT_FOUND, f"백업 파일을 찾을 수 없다: {backup_file.name}")

        try:
            conn = sqlite3.connect(str(backup_file), timeout=5.0)
            conn.row_factory = sqlite3.Row
            try:
                # 1. 파일 무결성 검사
                cursor = conn.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                if result is None or result[0] != "ok":
                    raise WikiError(
                        WikiErrorCode.VALIDATION_ERROR,
                        f"백업 파일의 무결성 검증 실패: {result[0] if result else 'unknown'}",
                    )

                # 2. 필수 테이블 존재 검사
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
                existing_tables = {row["name"] for row in cursor.fetchall()}
                required_tables = set(REQUIRED_TABLE_COLUMNS.keys())
                if not required_tables.issubset(existing_tables):
                    missing_tables = required_tables - existing_tables
                    raise WikiError(
                        WikiErrorCode.VALIDATION_ERROR,
                        f"백업 파일에 필수 테이블이 누락되었다: {missing_tables}",
                    )

                # 3. 스키마 버전 유효성 및 호환성 검사
                v_cursor = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version;")
                v_row = v_cursor.fetchone()
                backup_version = v_row[0] if v_row else 0
                if backup_version not in SUPPORTED_SCHEMA_VERSIONS:
                    raise WikiError(
                        WikiErrorCode.VALIDATION_ERROR,
                        f"지원하지 않는 백업 스키마 버전이다: {backup_version} (지원 버전: {sorted(SUPPORTED_SCHEMA_VERSIONS)})",
                    )

                # 4. 각 필수 테이블의 필수 컬럼 존재 검사
                for table_name, req_cols in REQUIRED_TABLE_COLUMNS.items():
                    info_cursor = conn.execute(f"PRAGMA table_info({table_name});")
                    col_names = {row["name"] for row in info_cursor.fetchall()}
                    if not req_cols.issubset(col_names):
                        missing_cols = req_cols - col_names
                        raise WikiError(
                            WikiErrorCode.VALIDATION_ERROR,
                            f"백업 파일의 {table_name} 테이블에 필수 컬럼이 누락되었다: {missing_cols}",
                        )

                # 5. 필수 외래 키 정의 검사 (B02: DDL에서 Foreign Key 제약 조건 누락 방지)
                for table_name, req_fks in REQUIRED_FOREIGN_KEYS.items():
                    fk_list_cursor = conn.execute(f"PRAGMA foreign_key_list({table_name});")
                    existing_fks = [
                        {"table": row["table"], "from": row["from"], "to": row["to"]}
                        for row in fk_list_cursor.fetchall()
                    ]
                    for req_fk in req_fks:
                        matched = any(
                            efk["table"] == req_fk["table"]
                            and efk["from"] == req_fk["from"]
                            and (req_fk["to"] is None or efk["to"] == req_fk["to"])
                            for efk in existing_fks
                        )
                        if not matched:
                            raise WikiError(
                                WikiErrorCode.VALIDATION_ERROR,
                                f"백업 파일의 {table_name} 테이블에 필수 외래 키 정의가 누락되었다: {req_fk}",
                            )

                # 6. 외래 키 제약 조건 및 데이터 관계 무결성 검사 (B02)
                conn.execute("PRAGMA foreign_keys = ON;")
                fk_cursor = conn.execute("PRAGMA foreign_key_check;")
                fk_violations = fk_cursor.fetchall()
                if fk_violations:
                    raise WikiError(
                        WikiErrorCode.VALIDATION_ERROR,
                        f"백업 파일에 외래 키 제약 조건 위반이 존재한다 ({len(fk_violations)}건)",
                    )
            finally:
                conn.close()
        except sqlite3.DatabaseError as exc:
            raise WikiError(
                WikiErrorCode.VALIDATION_ERROR,
                f"백업 파일이 유효한 SQLite 데이터베이스가 아니다: {exc}",
            ) from exc

    def restore_backup(self, backup_filename: str) -> None:
        """사전 검증 후 백업 파일로부터 활성 데이터베이스를 복원한다 (B02, B03).

        ARCHITECTURE.md §13, PRD FR-20 준수:
        - 백업 파일 이름 경로 검증 (Directory Traversal 방지)
        - 복원 전 스키마 및 외래 키 무결성 사전 검증 (B02)
        - WAL 모드의 최신 변경사항을 온전히 보존하는 일관된 스냅샷 기반 롤백 준비 (B03)
        - 복원 적용 실패와 복원 후 임시 파일 정리 실패의 엄격한 분리 (B03)
        - 실제 데이터 복원 확인 시에만 복구 성공 응답 반환
        """
        # Directory traversal 방지
        clean_filename = Path(backup_filename).name
        if clean_filename != backup_filename:
            raise WikiError(WikiErrorCode.VALIDATION_ERROR, f"유효하지 않은 백업 파일 이름이다: {backup_filename}")

        backup_file = self._backup_dir / clean_filename
        # B02: 복원 전 스키마, 컬럼, 외래키, 데이터 관계 철저 검증 (실패 시 원본 DB 절대 미변경)
        self.verify_backup_file(backup_file)

        # B03: 활성 DB 안전 보존 (WAL의 최신 변경을 포함하는 일관된 롤백 스냅샷)
        pre_restore = self._db_path.with_suffix(".pre_restore")
        has_existing = self._db_path.exists()
        if has_existing:
            active_conn = open_connection(self._db_path)
            try:
                # WAL checkpoint로 모든 미반영 프레임을 플러시한 후 온라인 백업으로 일관된 스냅샷 생성
                active_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                snapshot_conn = sqlite3.connect(str(pre_restore))
                try:
                    active_conn.backup(snapshot_conn)
                finally:
                    snapshot_conn.close()
            finally:
                active_conn.close()

        # 복원 수행 및 적용 실패 시 롤백
        restore_applied = False
        try:
            dest_conn = open_connection(self._db_path)
            try:
                src_conn = sqlite3.connect(str(backup_file))
                try:
                    src_conn.backup(dest_conn)
                finally:
                    src_conn.close()
                dest_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            finally:
                dest_conn.close()

            # 복원 후 복원된 DB 자체 검증
            self.verify_backup_file(self._db_path)
            restore_applied = True
        except Exception as exc:
            # 복원 적용 실패 시: 기존 일관된 스냅샷으로 롤백
            rollback_verified = False
            if has_existing and pre_restore.exists():
                try:
                    rb_dest = open_connection(self._db_path)
                    try:
                        rb_src = sqlite3.connect(str(pre_restore))
                        try:
                            rb_src.backup(rb_dest)
                        finally:
                            rb_src.close()
                        rb_dest.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                    finally:
                        rb_dest.close()
                    self.verify_backup_file(self._db_path)
                    rollback_verified = True
                except Exception as rb_exc:
                    logger.critical("복원 실패 후 롤백 중 치명적 오류 발생: %s", rb_exc)

            if rollback_verified:
                logger.error("Database restore failed, safely rolled back to original state: %s", exc)
                raise WikiError(
                    WikiErrorCode.READ_ERROR,
                    f"데이터베이스 복원 중 오류가 발생하여 기존 상태로 롤백했다: {exc}",
                ) from exc
            else:
                logger.critical("Database restore failed and rollback was not verified: %s", exc)
                raise WikiError(
                    WikiErrorCode.READ_ERROR,
                    f"데이터베이스 복원 중 오류가 발생했으며 기존 상태 복구에 실패했다: {exc}",
                ) from exc

        # B03: 복원 적용 성공 후 롤백용 임시 파일 정리
        # 정리 실패가 발생하더라도 데이터베이스 복원은 이미 성공했으므로 롤백하지 않는다.
        if restore_applied and pre_restore.exists():
            try:
                pre_restore.unlink(missing_ok=True)
            except Exception as cleanup_err:
                logger.warning("복원은 완료되었으나 롤백 임시 파일 정리 실패 (%s): %s", pre_restore.name, cleanup_err)

        logger.info("Successfully restored database from %s", clean_filename)
