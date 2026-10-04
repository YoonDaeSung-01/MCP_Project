"""TaskService 단위 테스트.

Task 생성, 상태 전이, 보관/복원, Revision 검증을 확인한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.db.models import TaskCreate, TaskStatus, TaskUpdate
from learning_app.services.task_service import TaskService
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


@pytest.fixture
def task_service(tmp_path: Path) -> TaskService:
    db_path = tmp_path / "task_test.sqlite"
    conn = open_connection(db_path)
    apply_migrations(conn)
    return TaskService(conn)


def test_create_and_get_task(task_service: TaskService) -> None:
    ref = {"type": "wiki", "note_id": "algorithms:02_해시_dict_set.md"}
    task = task_service.create_task(
        TaskCreate(title="해시 알고리즘 풀기", due_date="2026-10-10", target_ref=ref)
    )

    assert task.task_id
    assert task.title == "해시 알고리즘 풀기"
    assert task.status == TaskStatus.OPEN.value
    assert task.due_date == "2026-10-10"
    assert task.target_ref == ref
    assert task.revision == 1

    fetched = task_service.get_task(task.task_id)
    assert fetched.task_id == task.task_id
    assert fetched.target_ref == ref


def test_task_status_transition_and_archive_restore(task_service: TaskService) -> None:
    task = task_service.create_task(TaskCreate(title="공부하기"))
    assert task.status == TaskStatus.OPEN.value

    # 완료 처리
    done = task_service.update_task(
        task.task_id, TaskUpdate(expected_revision=1, status=TaskStatus.DONE.value)
    )
    assert done.status == TaskStatus.DONE.value
    assert done.revision == 2

    # 보관 처리 (archive)
    archived = task_service.archive_task(task.task_id, expected_revision=2)
    assert archived.status == TaskStatus.ARCHIVED.value
    assert archived.revision == 3

    # 목록 조회 시 상태 필터링 확인
    open_tasks = task_service.list_tasks(status=TaskStatus.OPEN.value)
    assert not any(t.task_id == task.task_id for t in open_tasks)

    archived_tasks = task_service.list_tasks(status=TaskStatus.ARCHIVED.value)
    assert any(t.task_id == task.task_id for t in archived_tasks)

    # 복원 처리 (restore -> open)
    restored = task_service.restore_task(task.task_id, expected_revision=3)
    assert restored.status == TaskStatus.OPEN.value
    assert restored.revision == 4


def test_task_revision_conflict(task_service: TaskService) -> None:
    task = task_service.create_task(TaskCreate(title="원본 태스크"))
    with pytest.raises(WikiError) as excinfo:
        task_service.update_task(
            task.task_id, TaskUpdate(expected_revision=99, title="잘못된 수정")
        )
    assert excinfo.value.code is WikiErrorCode.SOURCE_CHANGED
