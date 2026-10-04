"""Wiki 조회 오류. 오류 종류는 ARCHITECTURE §6의 계약 이름을 따른다."""

from __future__ import annotations

from enum import StrEnum


class WikiErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    SOURCE_CHANGED = "source_changed"
    PERMISSION_DENIED = "permission_denied"
    READ_ERROR = "read_error"


class WikiError(Exception):
    """종류가 있는 Wiki 오류. 메시지에 절대 File Path를 넣지 않는다."""

    def __init__(self, code: WikiErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
