"""변경 요청의 멱등성(Idempotency) 관리.

ARCHITECTURE.md §5 준수:
- request_id는 변경 요청과 Payload를 식별한다.
- 같은 ID와 같은 Payload의 재시도는 저장한 처리 결과를 반환한다.
- 같은 ID를 다른 Payload로 사용하면 validation_error를 반환한다.
- Transaction으로 변경과 처리 결과를 함께 저장한다.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Payload 딕셔너리의 결정론적 SHA-256 해시를 계산한다."""
    dumped = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def execute_with_idempotency(
    conn: sqlite3.Connection,
    request_id: str | None,
    payload: dict[str, Any],
    execute_fn: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """request_id를 검사하여 멱등적 실행 또는 이전 결과를 반환한다."""
    if not request_id:
        return execute_fn()

    payload_hash = compute_payload_hash(payload)

    # 기존 요청 확인
    cursor = conn.execute(
        "SELECT payload_hash, response_json FROM mutation_logs WHERE request_id = ?;",
        (request_id,),
    )
    row = cursor.fetchone()

    if row is not None:
        saved_hash, saved_response = row["payload_hash"], row["response_json"]
        if saved_hash == payload_hash:
            # 완전히 동일한 요청의 재시도: 기존 응답 반환
            return json.loads(saved_response)
        # 같은 ID인데 내용이 다른 요청: 충돌/검증 오류
        raise WikiError(
            WikiErrorCode.VALIDATION_ERROR,
            f"이미 다른 요청에 사용된 request_id이다: {request_id}",
        )

    # 새로운 요청: 실행 및 로그 기록 (호출자가 트랜잭션 관리)
    result = execute_fn()
    now_str = datetime.now(UTC).isoformat()
    conn.execute(
        """
        INSERT INTO mutation_logs (request_id, payload_hash, response_json, created_at)
        VALUES (?, ?, ?, ?);
        """,
        (request_id, payload_hash, json.dumps(result, ensure_ascii=False), now_str),
    )
    return result
