"""SessionService 단위 테스트.

세션 생성, active_context 갱신, 대화 Turn 기록 및 Cascade 삭제를 확인한다.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.db.models import SessionCreate, TurnCreate
from learning_app.services.session_service import SessionService
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


@pytest.fixture
def session_service(tmp_path: Path) -> SessionService:
    db_path = tmp_path / "session_test.sqlite"
    conn = open_connection(db_path)
    apply_migrations(conn)
    return SessionService(conn)


def test_create_session_and_add_turns(session_service: SessionService) -> None:
    session = session_service.create_session(
        SessionCreate(title="LLM 개념 학습", active_context={"study_unit_id": "unit-1"})
    )

    assert session.session_id
    assert session.title == "LLM 개념 학습"
    assert session.active_context == {"study_unit_id": "unit-1"}
    assert session.turns == []

    # 1. User turn 추가
    t1 = session_service.add_turn(
        session.session_id,
        TurnCreate(role="user", content="Transformer가 무엇인가요?"),
    )
    assert t1.turn_id
    assert t1.role == "user"
    assert t1.content == "Transformer가 무엇인가요?"

    # 2. Assistant turn 추가
    tool_calls = [{"tool": "search_notes", "args": {"query": "Transformer"}}]
    t2 = session_service.add_turn(
        session.session_id,
        TurnCreate(role="assistant", content="Transformer는 어텐션 메커니즘을 사용합니다.", tool_calls=tool_calls),
    )
    assert t2.turn_id
    assert t2.role == "assistant"
    assert t2.tool_calls == tool_calls

    # 세션 조회 시 turns 포함 확인
    fetched = session_service.get_session(session.session_id, include_turns=True)
    assert len(fetched.turns) == 2
    assert fetched.turns[0].turn_id == t1.turn_id
    assert fetched.turns[1].turn_id == t2.turn_id


def test_update_active_context(session_service: SessionService) -> None:
    session = session_service.create_session(SessionCreate(title="테스트 대화"))
    assert session.active_context == {}

    new_context = {"problem_key": "algo-hash-1", "hint_level": "concept"}
    updated = session_service.update_active_context(session.session_id, new_context)
    assert updated.active_context == new_context

    fetched = session_service.get_session(session.session_id)
    assert fetched.active_context == new_context


def test_delete_session_cascades_turns(session_service: SessionService) -> None:
    session = session_service.create_session(SessionCreate(title="삭제할 대화"))
    session_service.add_turn(session.session_id, TurnCreate(role="user", content="질문"))

    assert len(session_service.list_turns(session.session_id)) == 1

    session_service.delete_session(session.session_id)
    with pytest.raises(WikiError) as excinfo:
        session_service.get_session(session.session_id)
    assert excinfo.value.code is WikiErrorCode.NOT_FOUND

    # 턴 목록도 함께 삭제되었는지 확인
    assert session_service.list_turns(session.session_id) == []
