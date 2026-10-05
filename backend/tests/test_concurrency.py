"""동시성 및 트랜잭션 무결성 테스트 (B04).

ARCHITECTURE.md §5, PRD FR-07, FR-13, NF-01 준수:
- 20개의 동시 생성 요청이 SQLITE_BUSY_SNAPSHOT 없이 모두 성공 (20개 저장 확인)
- Revision 충돌 시 500 오류가 아닌 정의된 SOURCE_CHANGED(409) 반환
- request_id 멱등성 및 원자성 보장
"""

from __future__ import annotations

import concurrent.futures
from pathlib import Path

import pytest

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.db.models import PageCreate, PageUpdate, TaskCreate
from learning_app.services.page_service import PageService
from learning_app.services.task_service import TaskService
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


@pytest.fixture
def concurrent_db(tmp_path: Path):
    db_path = tmp_path / "concurrent_test.sqlite"
    init_conn = open_connection(db_path)
    apply_migrations(init_conn)
    init_conn.close()
    return db_path


def test_concurrent_page_creations_succeed_without_busy_snapshot(concurrent_db: Path) -> None:
    """B04: 20개의 동시 Page 생성 요청이 SQLITE_BUSY_SNAPSHOT 없이 모두 성공하고 20개 모두 저장된다."""
    num_requests = 20

    def create_page_worker(i: int):
        conn = open_connection(concurrent_db)
        try:
            page_svc = PageService(conn)
            page = page_svc.create_page(
                PageCreate(
                    title=f"동시 생성 페이지 {i}",
                    blocks=[{"type": "paragraph", "content": f"내용 {i}"}],
                )
            )
            return page.page_id
        finally:
            conn.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(create_page_worker, range(num_requests)))

    assert len(results) == num_requests
    assert len(set(results)) == num_requests  # 중복 없는 고유 ID

    # 검증: 실제 DB에 20개 모두 저장되었는지 확인
    check_conn = open_connection(concurrent_db)
    page_svc = PageService(check_conn)
    pages = page_svc.list_pages(limit=100)
    assert len(pages) == num_requests
    check_conn.close()


def test_concurrent_task_creations_succeed_without_busy_snapshot(concurrent_db: Path) -> None:
    """B04: 20개의 동시 Task 생성 요청이 누락 없이 모두 성공하고 저장된다."""
    num_requests = 20

    def create_task_worker(i: int):
        conn = open_connection(concurrent_db)
        try:
            task_svc = TaskService(conn)
            task = task_svc.create_task(
                TaskCreate(title=f"동시 생성 할 일 {i}")
            )
            return task.task_id
        finally:
            conn.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(create_task_worker, range(num_requests)))

    assert len(results) == num_requests
    assert len(set(results)) == num_requests

    check_conn = open_connection(concurrent_db)
    task_svc = TaskService(check_conn)
    tasks = task_svc.list_tasks(limit=100)
    assert len(tasks) == num_requests
    check_conn.close()


def test_concurrent_revision_conflict_returns_source_changed_defined_error(concurrent_db: Path) -> None:
    """B04: 동일 대상에 대해 같은 expected_revision으로 동시 수정을 시도할 때 1건만 성공하고 나머지는 SOURCE_CHANGED(409)로 처리된다."""
    # 1. 초기 문서 생성 (revision = 1)
    init_conn = open_connection(concurrent_db)
    page_svc = PageService(init_conn)
    page = page_svc.create_page(PageCreate(title="초기 문서", blocks=[]))
    init_conn.close()

    page_id = page.page_id
    successes: list[str] = []
    conflicts: list[str] = []
    unexpected_errors: list[str] = []

    def update_worker(worker_id: int):
        conn = open_connection(concurrent_db)
        try:
            svc = PageService(conn)
            res = svc.update_page(
                page_id,
                PageUpdate(
                    expected_revision=1,
                    title=f"작업자 {worker_id}의 수정",
                ),
            )
            successes.append(f"worker_{worker_id}")
            return res
        except WikiError as exc:
            if exc.code == WikiErrorCode.SOURCE_CHANGED:
                conflicts.append(f"worker_{worker_id}: {exc.message}")
            else:
                unexpected_errors.append(f"worker_{worker_id}: {exc}")
        except Exception as exc:
            unexpected_errors.append(f"worker_{worker_id}: {exc}")
        finally:
            conn.close()

    # 2개의 스레드가 동일한 expected_revision=1로 동시 업데이트
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(update_worker, i) for i in range(2)]
        concurrent.futures.wait(futures)

    assert len(unexpected_errors) == 0, f"예상치 못한 오류 발생: {unexpected_errors}"
    assert len(successes) == 1, f"성공은 정확히 1건이어야 함: {successes}"
    assert len(conflicts) == 1, f"충돌은 정의된 SOURCE_CHANGED로 1건이어야 함: {conflicts}"

    # 최종 DB 검증
    check_conn = open_connection(concurrent_db)
    final_page = PageService(check_conn).get_page(page_id)
    assert final_page.revision == 2
    check_conn.close()
