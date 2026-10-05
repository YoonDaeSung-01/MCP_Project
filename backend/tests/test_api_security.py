"""API 보안 및 출처 검증 테스트 (B01).

ARCHITECTURE.md §11, §13, PRD NF-02, FR-09 준수:
- Runtime Origin(http://127.0.0.1:5174)의 변경 요청(POST, PUT, PATCH, DELETE) 차단 (403 Forbidden)
- Runtime Origin에서 보낸 요청으로 Backup 및 사용자 데이터가 생성/변경되지 않음
- 정상 Frontend Origin(http://127.0.0.1:5173, http://localhost:5173)의 변경 요청 성공
- GET 조회 요청은 허용
"""

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
def security_client(tmp_path: Path):
    db_path = tmp_path / "security_test.sqlite"
    backup_dir = tmp_path / "backups"
    conn = open_connection(db_path)
    apply_migrations(conn)
    conn.close()

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
    app.dependency_overrides[get_wiki_service] = lambda: None

    client = TestClient(app)
    yield client, backup_dir, db_path
    app.dependency_overrides.clear()


def test_runtime_origin_mutating_requests_blocked_with_403(security_client) -> None:
    """B01: Runtime Origin(5174)에서 전송된 변경 요청은 403으로 차단되며 백업이나 데이터가 변경되지 않는다."""
    client, backup_dir, db_path = security_client

    runtime_headers = {"Origin": "http://127.0.0.1:5174"}

    # 1. 백업 생성 시도 차단
    res_backup = client.post("/api/backups", headers=runtime_headers)
    assert res_backup.status_code == 403
    assert res_backup.json()["code"] == "permission_denied"

    # 백업 파일이 실제로 생성되지 않았음을 확인
    backups = list(backup_dir.glob("*.sqlite"))
    assert len(backups) == 0

    # 2. 페이지 생성 시도 차단
    res_page = client.post(
        "/api/pages",
        headers=runtime_headers,
        json={"title": "런타임에서 시도한 페이지", "blocks": []},
    )
    assert res_page.status_code == 403
    assert res_page.json()["code"] == "permission_denied"

    # DB에 페이지가 저장되지 않았음을 확인
    check_conn = open_connection(db_path)
    cur = check_conn.execute("SELECT count(*) FROM pages;")
    assert cur.fetchone()[0] == 0
    check_conn.close()

    # 3. Task 생성 시도 차단 (localhost:5174 포함)
    res_task = client.post(
        "/api/tasks",
        headers={"Origin": "http://localhost:5174"},
        json={"title": "런타임 태스크"},
    )
    assert res_task.status_code == 403


def test_untrusted_cross_site_origin_blocked_with_403(security_client) -> None:
    """B01: 임의의 외부 출처(evil.com)에서의 변경 요청도 403으로 차단된다."""
    client, _, _ = security_client

    res = client.post(
        "/api/pages",
        headers={"Origin": "http://evil.com"},
        json={"title": "악성 페이지", "blocks": []},
    )
    assert res.status_code == 403
    assert res.json()["code"] == "permission_denied"


def test_legitimate_frontend_origins_allowed(security_client) -> None:
    """B01: 정상 프론트엔드 출처(127.0.0.1:5173, localhost:5173)의 변경 요청은 정상 처리된다."""
    client, _, db_path = security_client

    # 1. 127.0.0.1:5173
    res1 = client.post(
        "/api/pages",
        headers={"Origin": "http://127.0.0.1:5173"},
        json={"title": "정상 페이지 1", "blocks": []},
    )
    assert res1.status_code == 201

    # 2. localhost:5173
    res2 = client.post(
        "/api/pages",
        headers={"Origin": "http://localhost:5173"},
        json={"title": "정상 페이지 2", "blocks": []},
    )
    assert res2.status_code == 201

    # DB 확인
    check_conn = open_connection(db_path)
    cur = check_conn.execute("SELECT count(*) FROM pages;")
    assert cur.fetchone()[0] == 2
    check_conn.close()
