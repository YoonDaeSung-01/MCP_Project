"""FastAPI Pages, Tasks, Sessions, Backup API 엔드포인트 통합 테스트."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from learning_app.api.main import (
    app,
    get_backup_service,
    get_db_connection,
    get_wiki_service,
)
from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.services.backup_service import BackupService


@pytest.fixture
def storage_app(tmp_path: Path):
    db_path = tmp_path / "api_test.sqlite"
    backup_dir = tmp_path / "backups"
    conn = open_connection(db_path)
    apply_migrations(conn)

    def _override_db():
        c = open_connection(db_path)
        try:
            yield c
        finally:
            c.close()

    def _override_backup():
        return BackupService(db_path=db_path, backup_dir=backup_dir)

    app.dependency_overrides[get_db_connection] = _override_db
    app.dependency_overrides[get_backup_service] = _override_backup
    app.dependency_overrides[get_wiki_service] = lambda: None  # storage 테스트에는 필요 없음

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    conn.close()


def test_api_pages_crud_and_conflict(storage_app: TestClient) -> None:
    # 1. 생성
    create_res = storage_app.post(
        "/api/pages",
        json={"title": "새 페이지", "blocks": [{"type": "paragraph"}]},
    )
    assert create_res.status_code == 201
    page = create_res.json()
    page_id = page["page_id"]
    assert page["revision"] == 1

    # 2. 조회
    get_res = storage_app.get(f"/api/pages/{page_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "새 페이지"

    # 3. Revision 충돌 (expected_revision = 99) -> 409 Conflict
    conflict_res = storage_app.patch(
        f"/api/pages/{page_id}",
        json={"expected_revision": 99, "title": "충돌될 수정"},
    )
    assert conflict_res.status_code == 409
    assert conflict_res.json()["detail"]["code"] == "source_changed"

    # 4. 정상 수정 (expected_revision = 1) -> 200 OK, revision 2
    update_res = storage_app.patch(
        f"/api/pages/{page_id}",
        json={"expected_revision": 1, "title": "성공 수정"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["revision"] == 2
    assert update_res.json()["title"] == "성공 수정"


def test_api_tasks_archive_restore(storage_app: TestClient) -> None:
    # 1. 생성
    t_res = storage_app.post("/api/tasks", json={"title": "할 일 1"})
    assert t_res.status_code == 201
    task_id = t_res.json()["task_id"]

    # 2. 보관 (archive)
    arch_res = storage_app.post(
        f"/api/tasks/{task_id}/archive",
        json={"expected_revision": 1},
    )
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "archived"
    assert arch_res.json()["revision"] == 2

    # 3. 복원 (restore)
    rest_res = storage_app.post(
        f"/api/tasks/{task_id}/restore",
        json={"expected_revision": 2},
    )
    assert rest_res.status_code == 200
    assert rest_res.json()["status"] == "open"
    assert rest_res.json()["revision"] == 3


def test_api_sessions_and_turns(storage_app: TestClient) -> None:
    # 1. 세션 생성
    s_res = storage_app.post(
        "/api/sessions",
        json={"title": "대화방 1", "active_context": {"study_unit": "algo-1"}},
    )
    assert s_res.status_code == 201
    session_id = s_res.json()["session_id"]

    # 2. 턴 추가
    turn_res = storage_app.post(
        f"/api/sessions/{session_id}/turns",
        json={"role": "user", "content": "안녕하세요!"},
    )
    assert turn_res.status_code == 201
    assert turn_res.json()["role"] == "user"

    # 3. 세션 상세 조회 시 턴 포함 확인
    get_s = storage_app.get(f"/api/sessions/{session_id}")
    assert get_s.status_code == 200
    data = get_s.json()
    assert len(data["turns"]) == 1
    assert data["turns"][0]["content"] == "안녕하세요!"


def test_api_backup_create_and_list(storage_app: TestClient) -> None:
    # 백업 생성
    b_res = storage_app.post("/api/backups")
    assert b_res.status_code == 201
    data = b_res.json()
    assert data["filename"].startswith("backup_")

    # 백업 목록
    list_res = storage_app.get("/api/backups")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_api_restore_rejected_while_backend_running(storage_app: TestClient) -> None:
    """B03: 실행 중인 Backend에 대한 Restore API 요청은 App 종료 조건을 강제하여 409 Conflict로 거부된다."""
    # 1. 백업 생성
    b_res = storage_app.post("/api/backups")
    assert b_res.status_code == 201
    filename = b_res.json()["filename"]

    # 2. 실행 중인 상태에서 Restore 시도 -> 409 Conflict
    res = storage_app.post("/api/backups/restore", json={"filename": filename})
    assert res.status_code == 409
    err = res.json()["detail"]
    assert err["code"] == "conflict"
    assert "서버가 종료된 상태에서 오프라인으로 수행해야 한다" in err["message"]
