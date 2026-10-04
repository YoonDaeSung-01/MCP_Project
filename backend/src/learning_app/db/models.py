"""Page, Task, Session 데이터 모델 (DTO).

ARCHITECTURE.md §5 준수.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------- Page

class PageKind(StrEnum):
    PAGE = "page"
    CODING_RECORD = "coding_record"


class PageDTO(_Frozen):
    page_id: str
    kind: str = PageKind.PAGE
    title: str
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    revision: int = 1
    created_at: str
    updated_at: str


class PageCreate(BaseModel):
    title: str
    kind: str = PageKind.PAGE
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class PageUpdate(BaseModel):
    expected_revision: int
    title: str | None = None
    blocks: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
    request_id: str | None = None


# ---------------------------------------------------------------- Task

class TaskStatus(StrEnum):
    OPEN = "open"
    DONE = "done"
    ARCHIVED = "archived"


class TaskDTO(_Frozen):
    task_id: str
    title: str
    status: str = TaskStatus.OPEN
    due_date: str | None = None
    target_ref: dict[str, Any] | None = None
    revision: int = 1
    created_at: str
    updated_at: str


class TaskCreate(BaseModel):
    title: str
    due_date: str | None = None
    target_ref: dict[str, Any] | None = None
    request_id: str | None = None


class TaskUpdate(BaseModel):
    expected_revision: int
    title: str | None = None
    status: str | None = None
    due_date: str | None = None
    target_ref: dict[str, Any] | None = None
    request_id: str | None = None


# ---------------------------------------------------------------- Session & Turn

class TurnRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class TurnStatus(StrEnum):
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


class TurnDTO(_Frozen):
    turn_id: str
    session_id: str
    role: str
    content: str
    status: str = TurnStatus.DONE
    tool_calls: list[dict[str, Any]] | None = None
    created_at: str


class TurnCreate(BaseModel):
    role: str
    content: str
    status: str = TurnStatus.DONE
    tool_calls: list[dict[str, Any]] | None = None


class SessionDTO(_Frozen):
    session_id: str
    title: str
    active_context: dict[str, Any] = Field(default_factory=dict)
    turns: list[TurnDTO] = Field(default_factory=list)
    created_at: str
    updated_at: str


class SessionCreate(BaseModel):
    title: str
    active_context: dict[str, Any] = Field(default_factory=dict)
