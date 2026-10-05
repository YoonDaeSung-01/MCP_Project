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


def test_restore_incompatible_schema_version_rejected_and_preserves_data(backup_env) -> None:
    """B02: schema_version이 999 등 지원하지 않는 버전인 경우 복원을 거부하고 원본 데이터를 보존한다."""
    db_path, backup_dir, backup_service = backup_env

    # 1. 원본 데이터 생성
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p = page_svc.create_page(PageCreate(title="버전 거부 시 보존될 문서"))
    conn.close()

    # 2. 유효한 백업 파일 생성 후 schema_version만 999로 조작
    valid_backup = backup_service.create_backup()
    bad_backup_path = backup_dir / "backup_v999.sqlite"
    import shutil
    shutil.copy2(backup_dir / valid_backup["filename"], bad_backup_path)

    bad_conn = sqlite3.connect(str(bad_backup_path))
    bad_conn.execute("UPDATE schema_version SET version = 999;")
    bad_conn.commit()
    bad_conn.close()

    # 3. 복원 시도 -> validation_error
    with pytest.raises(WikiError) as excinfo:
        backup_service.restore_backup("backup_v999.sqlite")
    assert excinfo.value.code is WikiErrorCode.VALIDATION_ERROR
    assert "지원하지 않는 백업 스키마 버전" in excinfo.value.message

    # 4. 원본 데이터 보존 확인
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    assert page_svc.get_page(p.page_id).title == "버전 거부 시 보존될 문서"
    conn.close()


def test_restore_missing_columns_rejected_and_preserves_data(backup_env) -> None:
    """B02: 필수 컬럼이 누락되거나 더미 컬럼만 있는 백업은 복원을 거부하고 원본 데이터를 보존한다."""
    db_path, backup_dir, backup_service = backup_env

    # 1. 원본 데이터 생성
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p = page_svc.create_page(PageCreate(title="컬럼 누락 거부 시 보존될 문서"))
    conn.close()

    # 2. 필수 컬럼이 누락된 백업 파일 생성
    bad_backup_path = backup_dir / "backup_bad_columns.sqlite"
    bad_conn = sqlite3.connect(str(bad_backup_path))
    bad_conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT);")
    bad_conn.execute("INSERT INTO schema_version VALUES (1, 'now');")
    bad_conn.execute("CREATE TABLE pages (page_id TEXT PRIMARY KEY, dummy TEXT);")
    bad_conn.execute("CREATE TABLE tasks (task_id TEXT PRIMARY KEY, dummy TEXT);")
    bad_conn.execute("CREATE TABLE sessions (session_id TEXT PRIMARY KEY, dummy TEXT);")
    bad_conn.execute("CREATE TABLE turns (turn_id TEXT PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, status TEXT, tool_calls TEXT, created_at TEXT);")
    bad_conn.execute("CREATE TABLE mutation_logs (request_id TEXT PRIMARY KEY, payload_hash TEXT, response_json TEXT, created_at TEXT);")
    bad_conn.commit()
    bad_conn.close()

    # 3. 복원 시도 -> validation_error
    with pytest.raises(WikiError) as excinfo:
        backup_service.restore_backup("backup_bad_columns.sqlite")
    assert excinfo.value.code is WikiErrorCode.VALIDATION_ERROR
    assert "필수 컬럼이 누락되었다" in excinfo.value.message

    # 4. 원본 데이터 보존 확인
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    assert page_svc.get_page(p.page_id).title == "컬럼 누락 거부 시 보존될 문서"
    conn.close()


def test_restore_foreign_key_violation_rejected_and_preserves_data(backup_env) -> None:
    """B02: 외래 키 제약 조건 위반(예: 존재하지 않는 session_id를 참조하는 turn)이 있는 백업은 복원을 거부한다."""
    db_path, backup_dir, backup_service = backup_env

    # 1. 원본 데이터 생성
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p = page_svc.create_page(PageCreate(title="FK 위반 거부 시 보존될 문서"))
    conn.close()

    # 2. 정상 백업 복사 후 FK 위반 데이터 주입
    valid_backup = backup_service.create_backup()
    fk_backup_path = backup_dir / "backup_fk_violation.sqlite"
    import shutil
    shutil.copy2(backup_dir / valid_backup["filename"], fk_backup_path)

    bad_conn = sqlite3.connect(str(fk_backup_path))
    # PRAGMA foreign_keys = OFF 상태에서 위반 데이터 삽입
    bad_conn.execute("PRAGMA foreign_keys = OFF;")
    bad_conn.execute(
        """
        INSERT INTO turns (turn_id, session_id, role, content, status, tool_calls, created_at)
        VALUES ('turn-orphan', 'session-nonexistent', 'user', 'hello', 'done', NULL, 'now');
        """
    )
    bad_conn.commit()
    bad_conn.close()

    # 3. 복원 시도 -> validation_error
    with pytest.raises(WikiError) as excinfo:
        backup_service.restore_backup("backup_fk_violation.sqlite")
    assert excinfo.value.code is WikiErrorCode.VALIDATION_ERROR
    assert "외래 키 제약 조건 위반" in excinfo.value.message

    # 4. 원본 데이터 보존 확인
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    assert page_svc.get_page(p.page_id).title == "FK 위반 거부 시 보존될 문서"
    conn.close()


def test_restore_foreign_key_definition_missing_rejected_and_preserves_data(backup_env) -> None:
    """B02: 컬럼과 버전은 일치하지만 DDL에 외래 키 제약 조건 정의가 누락된 백업은 복원을 거부하고 원본을 보존한다."""
    db_path, backup_dir, backup_service = backup_env

    # 1. 원본 데이터 생성
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p = page_svc.create_page(PageCreate(title="FK 정의 누락 거부 시 보존될 문서"))
    conn.close()

    # 2. 필수 테이블과 컬럼, 버전은 모두 갖추었으나 turns의 외래키 REFERENCES sessions(session_id) 정의가 누락된 백업 생성
    missing_fk_backup_path = backup_dir / "backup_missing_fk_def.sqlite"
    bad_conn = sqlite3.connect(str(missing_fk_backup_path))
    bad_conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT);")
    bad_conn.execute("INSERT INTO schema_version VALUES (1, 'now');")
    bad_conn.execute(
        """
        CREATE TABLE pages (
            page_id TEXT PRIMARY KEY, kind TEXT, title TEXT, blocks TEXT, metadata TEXT,
            revision INTEGER, created_at TEXT, updated_at TEXT
        );
        """
    )
    bad_conn.execute(
        """
        CREATE TABLE tasks (
            task_id TEXT PRIMARY KEY, title TEXT, status TEXT, due_date TEXT,
            target_ref TEXT, revision INTEGER, created_at TEXT, updated_at TEXT
        );
        """
    )
    bad_conn.execute(
        """
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY, title TEXT, active_context TEXT,
            created_at TEXT, updated_at TEXT
        );
        """
    )
    # FK 정의 없이 생성된 turns 테이블
    bad_conn.execute(
        """
        CREATE TABLE turns (
            turn_id TEXT PRIMARY KEY, session_id TEXT, role TEXT, content TEXT,
            status TEXT, tool_calls TEXT, created_at TEXT
        );
        """
    )
    bad_conn.execute(
        """
        CREATE TABLE mutation_logs (
            request_id TEXT PRIMARY KEY, payload_hash TEXT, response_json TEXT, created_at TEXT
        );
        """
    )
    # 외래키 정의가 없으므로 PRAGMA foreign_key_check로는 잡히지 않는 고아 turn 데이터 삽입
    bad_conn.execute(
        """
        INSERT INTO turns (turn_id, session_id, role, content, status, tool_calls, created_at)
        VALUES ('turn-orphan-no-fk', 'session-ghost', 'user', 'hi', 'done', NULL, 'now');
        """
    )
    bad_conn.commit()
    bad_conn.close()

    # 3. 복원 시도 -> validation_error (외래 키 정의 누락 감지)
    with pytest.raises(WikiError) as excinfo:
        backup_service.restore_backup("backup_missing_fk_def.sqlite")
    assert excinfo.value.code is WikiErrorCode.VALIDATION_ERROR
    assert "필수 외래 키 정의가 누락되었다" in excinfo.value.message

    # 4. 원본 데이터 보존 확인
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    assert page_svc.get_page(p.page_id).title == "FK 정의 누락 거부 시 보존될 문서"
    conn.close()


def test_restore_with_wal_preserves_latest_data_on_failure(backup_env, monkeypatch) -> None:
    """B03: WAL에 최신 변경이 남아있는 상태(Connection 유지)에서 복원 실패 시 일관된 롤백 스냅샷으로 최신 데이터가 온전히 보존된다."""
    db_path, backup_dir, backup_service = backup_env

    # 1. 초기 1개 문서로 백업 생성
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p1 = page_svc.create_page(PageCreate(title="초기 문서 1"))
    conn.close()

    old_backup = backup_service.create_backup()

    # 2. 활성 DB에 새 문서 추가 (Connection을 닫지 않고 유지하여 WAL 프레임 활성 상태 유지)
    active_conn = open_connection(db_path)
    page_svc = PageService(active_conn)
    p2 = page_svc.create_page(PageCreate(title="WAL에만 있는 최신 문서 2"))
    assert len(page_svc.list_pages()) == 2
    # Connection을 닫지 않고 유지하여 WAL이 체크포인트로 사전 정리되지 않도록 함

    # 3. 복원 적용 후 검증 단계에서 실패 주입 (손상된 복원 적용 상황 모사)
    orig_verify = backup_service.verify_backup_file
    verify_calls = {"count": 0}

    def failing_verify(p):
        verify_calls["count"] += 1
        # call 1: 복원 시작 전 backup_file 사전 검증 (성공)
        # call 2: 복원 적용 후 self._db_path 검증 (여기서 실패 주입 -> 롤백 트리거)
        # call 3: 롤백 후 self._db_path 검증 (성공해야 함)
        if verify_calls["count"] == 2:
            raise RuntimeError("주입된 복원 적용 후 무결성 실패")
        return orig_verify(p)

    monkeypatch.setattr(backup_service, "verify_backup_file", failing_verify)

    try:
        with pytest.raises(WikiError) as excinfo:
            backup_service.restore_backup(old_backup["filename"])
        assert excinfo.value.code is WikiErrorCode.READ_ERROR
        assert "기존 상태로 롤백했다" in excinfo.value.message
    finally:
        active_conn.close()

    # 4. 검증: WAL의 최신 변경사항이었던 p2를 포함하여 2개 문서 모두 온전히 보존되었는지 확인
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    pages = page_svc.list_pages()
    assert len(pages) == 2
    titles = {p.title for p in pages}
    assert "초기 문서 1" in titles
    assert "WAL에만 있는 최신 문서 2" in titles
    conn.close()


def test_restore_cleanup_failure_does_not_rollback_successful_restore(backup_env, monkeypatch) -> None:
    """B03: 복원 적용이 성공한 후 임시 파일 정리(unlink)가 실패하더라도 복원을 번복하지 않고 성공으로 유지한다."""
    db_path, backup_dir, backup_service = backup_env

    # 1. 초기 1개 문서로 백업 생성
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p1 = page_svc.create_page(PageCreate(title="백업에 저장된 문서"))
    conn.close()

    backup_info = backup_service.create_backup()

    # 2. 활성 DB에 임시 문서 추가 (복원 후 사라져야 하는 문서)
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    p2 = page_svc.create_page(PageCreate(title="임시 문서"))
    assert len(page_svc.list_pages()) == 2
    conn.close()

    # 3. .pre_restore 임시 파일 정리 시 PermissionError(Windows 파일 잠금) 1회 주입
    orig_unlink = Path.unlink

    def mock_unlink(self, missing_ok=False):
        if str(self).endswith(".pre_restore"):
            raise PermissionError("Windows 파일 잠금으로 임시 파일 삭제 실패")
        return orig_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", mock_unlink)

    # 4. 복원 실행: 임시 파일 정리가 실패해도 예외 없이 정상 복원 완료되어야 함
    backup_service.restore_backup(backup_info["filename"])

    # 5. 검증: 복원이 유지되어 p1만 존재하고 p2는 없어야 함 (정리 실패로 롤백되지 않음)
    conn = open_connection(db_path)
    page_svc = PageService(conn)
    pages = page_svc.list_pages()
    assert len(pages) == 1
    assert pages[0].title == "백업에 저장된 문서"
    conn.close()
