"""Backup & Restore 단위 테스트.

백업 파일 생성, 무결성 사전 검증, 데이터 복원 및 실패 시 롤백을 확인한다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.db.models import PageCreate
from learning_app.services.backup_service import BackupService
from learning_app.services.page_service import PageService
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


@pytest.fixture
def backup_env(tmp_path: Path):
    db_path = tmp_path / "active.sqlite"
    backup_dir = tmp_path / "backups"
    conn = open_connection(db_path)
    apply_migrations(conn)
    conn.close()

    service = BackupService(db_path=db_path, backup_dir=backup_dir)
    return db_path, backup_dir, service


def test_create_and_list_backup(backup_env) -> None:
    db_path, backup_dir, backup_service = backup_env

    # 1. 백업 생성
    info = backup_service.create_backup()
    assert info["filename"].startswith("backup_")
    assert info["size_bytes"] > 0
    assert (backup_dir / info["filename"]).exists()

    # 2. 백업 목록 확인
    backups = backup_service.list_backups()
    assert len(backups) == 1
    assert backups[0]["filename"] == info["filename"]


def test_restore_backup_restores_exact_state(backup_env) -> None:
    db_path, backup_dir, backup_service = backup_env

    # 1. 초기 데이터 저장
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p1 = page_svc.create_page(PageCreate(title="초기 문서", blocks=[]))
    conn.close()

    # 2. 백업 생성
    info = backup_service.create_backup()

    # 3. 데이터 변경 (새 문서 추가, 기존 문서 삭제)
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    page_svc.create_page(PageCreate(title="임시 문서"))
    page_svc.delete_page(p1.page_id)
    conn.close()

    # 4. 복원 실행
    backup_service.restore_backup(info["filename"])

    # 5. 복원 후 검증: p1이 다시 존재하고, 임시 문서는 없어야 함
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    restored_p1 = page_svc.get_page(p1.page_id)
    assert restored_p1.title == "초기 문서"
    all_pages = page_svc.list_pages()
    assert len(all_pages) == 1
    conn.close()


def test_restore_corrupt_file_is_rejected_and_preserves_original(backup_env) -> None:
    db_path, backup_dir, backup_service = backup_env

    # 1. 원본 데이터 생성
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p = page_svc.create_page(PageCreate(title="보존될 원본 문서"))
    conn.close()

    # 2. 손상된 가짜 백업 파일 생성
    fake_backup = backup_dir / "backup_corrupt.sqlite"
    fake_backup.write_bytes(b"THIS IS NOT A SQLITE FILE")

    # 3. 복원 시도 -> validation_error
    with pytest.raises(WikiError) as excinfo:
        backup_service.restore_backup("backup_corrupt.sqlite")
    assert excinfo.value.code is WikiErrorCode.VALIDATION_ERROR

    # 4. 기존 원본 데이터가 손상 없이 유지되었는지 확인
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    assert page_svc.get_page(p.page_id).title == "보존될 원본 문서"
    conn.close()
