"""PageService 단위 테스트.

Revision 검증, 충돌 처리, 멱등성 및 Block JSON 보존을 확인한다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.db.models import PageCreate, PageUpdate
from learning_app.services.page_service import PageService
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


@pytest.fixture
def page_service(tmp_path: Path) -> PageService:
    db_path = tmp_path / "page_test.sqlite"
    conn = open_connection(db_path)
    apply_migrations(conn)
    return PageService(conn)


def test_create_and_get_page(page_service: PageService) -> None:
    blocks = [
        {"type": "heading", "props": {"level": 1}, "content": "내 학습 노트"},
        {"type": "paragraph", "content": "본문 내용입니다."},
    ]
    meta = {"source_ref": "ai_terms:wiki/01_원리/LLM.md"}

    page = page_service.create_page(
        PageCreate(title="LLM 학습 기록", blocks=blocks, metadata=meta)
    )

    assert page.page_id
    assert page.title == "LLM 학습 기록"
    assert page.blocks == blocks
    assert page.metadata == meta
    assert page.revision == 1

    fetched = page_service.get_page(page.page_id)
    assert fetched.page_id == page.page_id
    assert fetched.blocks == blocks
    assert fetched.revision == 1


def test_update_page_and_revision_increment(page_service: PageService) -> None:
    page = page_service.create_page(PageCreate(title="초기 제목", blocks=[]))
    assert page.revision == 1

    # 정상 업데이트: expected_revision == 1 -> revision 2로 증가
    updated = page_service.update_page(
        page.page_id,
        PageUpdate(expected_revision=1, title="수정된 제목", blocks=[{"type": "p"}]),
    )
    assert updated.title == "수정된 제목"
    assert updated.revision == 2
    assert updated.blocks == [{"type": "p"}]

    # 다시 업데이트: expected_revision == 2 -> revision 3으로 증가
    updated2 = page_service.update_page(
        page.page_id,
        PageUpdate(expected_revision=2, title="두 번째 수정"),
    )
    assert updated2.revision == 3
    assert updated2.title == "두 번째 수정"
    assert updated2.blocks == [{"type": "p"}]  # 미지정 필드 보존 확인


def test_update_page_revision_conflict(page_service: PageService) -> None:
    page = page_service.create_page(PageCreate(title="원본", blocks=[]))
    assert page.revision == 1

    # expected_revision을 잘못 지정한 경우 -> source_changed 발생
    with pytest.raises(WikiError) as excinfo:
        page_service.update_page(
            page.page_id,
            PageUpdate(expected_revision=99, title="잘못된 수정"),
        )
    assert excinfo.value.code is WikiErrorCode.SOURCE_CHANGED

    # 이미 2로 업데이트된 후 이전 1로 요청한 경우 -> source_changed 발생
    page_service.update_page(page.page_id, PageUpdate(expected_revision=1, title="1차 수정"))
    with pytest.raises(WikiError) as excinfo:
        page_service.update_page(page.page_id, PageUpdate(expected_revision=1, title="지연된 1차 수정"))
    assert excinfo.value.code is WikiErrorCode.SOURCE_CHANGED


def test_list_and_delete_page(page_service: PageService) -> None:
    p1 = page_service.create_page(PageCreate(title="Page 1", kind="page"))
    p2 = page_service.create_page(PageCreate(title="Page 2", kind="coding_record"))

    all_pages = page_service.list_pages()
    assert len(all_pages) == 2

    records_only = page_service.list_pages(kind="coding_record")
    assert len(records_only) == 1
    assert records_only[0].page_id == p2.page_id

    page_service.delete_page(p1.page_id)
    with pytest.raises(WikiError) as excinfo:
        page_service.get_page(p1.page_id)
    assert excinfo.value.code is WikiErrorCode.NOT_FOUND
