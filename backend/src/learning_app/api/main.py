"""FastAPI application entrypoint and API routes.

- Wiki API (/api/wiki)
- Pages API (/api/pages)
- Tasks API (/api/tasks)
- Sessions API (/api/sessions)
- Backup API (/api/backups)
"""

from __future__ import annotations

import sqlite3
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Body, Depends, FastAPI, HTTPException, Path as FastPath, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations
from learning_app.db.models import (
    PageCreate,
    PageDTO,
    PageUpdate,
    SessionCreate,
    SessionDTO,
    TaskCreate,
    TaskDTO,
    TaskUpdate,
    TurnCreate,
    TurnDTO,
)
from learning_app.integrations.wiki_mcp_client import WikiMCPClient
from learning_app.services.backup_service import BackupService
from learning_app.services.page_service import PageService
from learning_app.services.session_service import SessionService
from learning_app.services.task_service import TaskService
from learning_app.services.wiki_service import WikiService
from learning_app.settings import Settings, get_settings
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode

_wiki_client: WikiMCPClient | None = None
_wiki_service: WikiService | None = None


# ---------------------------------------------------------------- Dependencies

def get_db_path() -> Path:
    settings = get_settings()
    data_dir = settings.get_data_dir()
    return data_dir / "app.sqlite"


def get_backup_dir() -> Path:
    settings = get_settings()
    data_dir = settings.get_data_dir()
    return data_dir / "backups"


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """SQLite 데이터베이스 연결을 생성하고 반환한다."""
    db_path = get_db_path()
    conn = open_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_page_service(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> PageService:
    return PageService(conn)


def get_task_service(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> TaskService:
    return TaskService(conn)


def get_session_service(
    conn: Annotated[sqlite3.Connection, Depends(get_db_connection)],
) -> SessionService:
    return SessionService(conn)


def get_backup_service() -> BackupService:
    return BackupService(db_path=get_db_path(), backup_dir=get_backup_dir())


def get_wiki_service() -> WikiService:
    """WikiService 인스턴스를 반환한다 (FastAPI Dependency)."""
    global _wiki_service, _wiki_client
    if _wiki_service is None:
        if _wiki_client is None:
            _wiki_client = WikiMCPClient(get_settings())
        _wiki_service = WikiService(_wiki_client)
    return _wiki_service


# ---------------------------------------------------------------- Lifespan

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 기동 시 DB 마이그레이션을 확인하고 종료 시 Wiki MCP Client를 닫는다."""
    # 앱 기동 시 DB 초기화 확인
    db_path = get_db_path()
    init_conn = open_connection(db_path)
    try:
        apply_migrations(init_conn)
    finally:
        init_conn.close()

    yield

    global _wiki_client, _wiki_service
    if _wiki_client is not None:
        await _wiki_client.close()
        _wiki_client = None
        _wiki_service = None


app = FastAPI(
    title="Learning App API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://localhost:5173",
}
FORBIDDEN_ORIGINS = {
    "http://127.0.0.1:5174",
    "http://localhost:5174",
}
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def validate_origin_and_csrf(request: Request, call_next):
    """HTTP 변경 요청(POST, PUT, PATCH, DELETE)의 Origin 및 CSRF 검증 (B01).

    ARCHITECTURE.md §11, §13 및 PRD NF-02, FR-09 준수:
    - Runtime Origin(5174) 등 허용되지 않은 Origin에서의 변경 요청 차단 (403 Forbidden)
    - simple POST 및 no-cors 요청을 통한 무단 Backup 생성 및 데이터 변조 방지
    """
    if request.method in MUTATING_METHODS:
        origin = request.headers.get("origin")
        # 1. 런타임 Origin(5174) 등 명시적 금지 출처 차단
        if origin in FORBIDDEN_ORIGINS:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "code": "permission_denied",
                    "message": f"허용되지 않은 Origin({origin})에서의 변경 요청이다.",
                },
            )
        # 2. Origin 헤더가 존재하지만 허용 목록에 없는 경우 차단 (CORS simple POST 및 no-cors 방어)
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "code": "permission_denied",
                    "message": f"허용되지 않은 Origin({origin})에서의 변경 요청이다.",
                },
            )
        # 3. Sec-Fetch-Site가 cross-site이면서 허용되지 않은 출처인 경우 차단
        sec_fetch_site = request.headers.get("sec-fetch-site")
        if sec_fetch_site == "cross-site" and (not origin or origin not in ALLOWED_ORIGINS):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "code": "permission_denied",
                    "message": "교차 출처(cross-site)에서의 변경 요청은 허용되지 않는다.",
                },
            )
    return await call_next(request)


def _handle_wiki_error(exc: WikiError) -> HTTPException:
    status_map = {
        WikiErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        WikiErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        WikiErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
        WikiErrorCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
        WikiErrorCode.SOURCE_CHANGED: status.HTTP_409_CONFLICT,
        WikiErrorCode.READ_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    status_code = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code.value, "message": exc.message},
    )


# ---------------------------------------------------------------- Health

@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


# ---------------------------------------------------------------- Wiki API

@app.get("/api/wiki/notes")
async def get_wiki_notes(
    query: str | None = Query(default=None, description="검색어"),
    collection: str | None = Query(default=None, description="Collection 식별자"),
    cursor: str | None = Query(default=None, description="Pagination 커서"),
    limit: int | None = Query(default=None, description="최대 조회 개수"),
    service: Annotated[WikiService, Depends(get_wiki_service)] = None,  # type: ignore
) -> dict[str, Any]:
    try:
        if query:
            res = await service.search_notes(query=query, collection=collection, limit=limit)
            return res.model_dump(mode="json")
        res = await service.list_notes(collection=collection, cursor=cursor, limit=limit)
        return res.model_dump(mode="json")
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/wiki/headings")
async def get_wiki_headings(
    note_id: str = Query(..., description="Note ID 식별자"),
    service: Annotated[WikiService, Depends(get_wiki_service)] = None,  # type: ignore
) -> dict[str, Any]:
    try:
        res = await service.get_headings(note_id=note_id)
        return res.model_dump(mode="json")
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/wiki/note")
async def get_wiki_note(
    note_id: str = Query(..., description="Note ID 식별자"),
    section_id: str | None = Query(default=None, description="Section ID"),
    file_version: str | None = Query(default=None, description="검증할 파일 버전 해시"),
    cursor: str | None = Query(default=None, description="읽기 커서"),
    service: Annotated[WikiService, Depends(get_wiki_service)] = None,  # type: ignore
) -> dict[str, Any]:
    try:
        res = await service.read_note(
            note_id=note_id,
            section_id=section_id,
            file_version=file_version,
            cursor=cursor,
        )
        return res.model_dump(mode="json")
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/wiki/index")
async def get_wiki_index(
    service: Annotated[WikiService, Depends(get_wiki_service)] = None,  # type: ignore
) -> dict[str, Any]:
    try:
        return await service.get_index()
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


# ---------------------------------------------------------------- Page API

@app.post("/api/pages", status_code=status.HTTP_201_CREATED)
async def create_page(
    data: PageCreate,
    service: Annotated[PageService, Depends(get_page_service)],
) -> PageDTO:
    try:
        return service.create_page(data)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/pages/{page_id}")
async def get_page(
    page_id: str = FastPath(..., description="Page ID"),
    service: Annotated[PageService, Depends(get_page_service)] = None,  # type: ignore
) -> PageDTO:
    try:
        return service.get_page(page_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/pages")
async def list_pages(
    kind: str | None = Query(default=None, description="문서 종류 필터 (page, coding_record)"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: Annotated[PageService, Depends(get_page_service)] = None,  # type: ignore
) -> list[PageDTO]:
    try:
        return service.list_pages(kind=kind, limit=limit, offset=offset)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.patch("/api/pages/{page_id}")
async def update_page(
    page_id: str,
    data: PageUpdate,
    service: Annotated[PageService, Depends(get_page_service)],
) -> PageDTO:
    try:
        return service.update_page(page_id, data)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.delete("/api/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: str,
    service: Annotated[PageService, Depends(get_page_service)],
) -> None:
    try:
        service.delete_page(page_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


# ---------------------------------------------------------------- Task API

@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskDTO:
    try:
        return service.create_task(data)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/tasks/{task_id}")
async def get_task(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskDTO:
    try:
        return service.get_task(task_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/tasks")
async def list_tasks(
    status: str | None = Query(default=None, description="상태 필터 (open, done, archived)"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: Annotated[TaskService, Depends(get_task_service)] = None,  # type: ignore
) -> list[TaskDTO]:
    try:
        return service.list_tasks(status=status, limit=limit, offset=offset)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: str,
    data: TaskUpdate,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskDTO:
    try:
        return service.update_task(task_id, data)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.post("/api/tasks/{task_id}/archive")
async def archive_task(
    task_id: str,
    expected_revision: int = Body(..., embed=True),
    request_id: str | None = Body(default=None, embed=True),
    service: Annotated[TaskService, Depends(get_task_service)] = None,  # type: ignore
) -> TaskDTO:
    try:
        return service.archive_task(task_id, expected_revision=expected_revision, request_id=request_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.post("/api/tasks/{task_id}/restore")
async def restore_task(
    task_id: str,
    expected_revision: int = Body(..., embed=True),
    request_id: str | None = Body(default=None, embed=True),
    service: Annotated[TaskService, Depends(get_task_service)] = None,  # type: ignore
) -> TaskDTO:
    try:
        return service.restore_task(task_id, expected_revision=expected_revision, request_id=request_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    try:
        service.delete_task(task_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


# ---------------------------------------------------------------- Session API

@app.post("/api/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionDTO:
    try:
        return service.create_session(data)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/sessions/{session_id}")
async def get_session(
    session_id: str,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionDTO:
    try:
        return service.get_session(session_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/sessions")
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: Annotated[SessionService, Depends(get_session_service)] = None,  # type: ignore
) -> list[SessionDTO]:
    try:
        return service.list_sessions(limit=limit, offset=offset)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.patch("/api/sessions/{session_id}/context")
async def update_session_context(
    session_id: str,
    active_context: dict[str, Any],
    service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionDTO:
    try:
        return service.update_active_context(session_id, active_context)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.post("/api/sessions/{session_id}/turns", status_code=status.HTTP_201_CREATED)
async def add_turn(
    session_id: str,
    data: TurnCreate,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> TurnDTO:
    try:
        return service.add_turn(session_id, data)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/sessions/{session_id}/turns")
async def list_turns(
    session_id: str,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> list[TurnDTO]:
    try:
        return service.list_turns(session_id)
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


# ---------------------------------------------------------------- Backup API

@app.post("/api/backups", status_code=status.HTTP_201_CREATED)
async def create_backup(
    service: Annotated[BackupService, Depends(get_backup_service)],
) -> dict[str, Any]:
    try:
        return service.create_backup()
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/backups")
async def list_backups(
    service: Annotated[BackupService, Depends(get_backup_service)],
) -> list[dict[str, Any]]:
    try:
        return service.list_backups()
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.post("/api/backups/restore")
async def restore_backup(
    filename: str = Body(..., embed=True),
    service: Annotated[BackupService, Depends(get_backup_service)] = None,  # type: ignore
) -> dict[str, str]:
    """백업 복원 요청을 처리한다.

    ARCHITECTURE.md §13, PRD FR-20 준수:
    - 데이터베이스 복원은 서버(App)가 완전히 종료된 상태에서 오프라인으로만 수행해야 한다.
    - 실행 중인 Backend에서 라이브 복원을 시도하면 충돌(409 Conflict) 오류를 반환하여 데이터 손상을 방지한다.
    """
    raise _handle_wiki_error(
        WikiError(
            WikiErrorCode.CONFLICT,
            "데이터베이스 복원은 서버가 종료된 상태에서 오프라인으로 수행해야 한다 (ARCHITECTURE §13, PRD FR-20)",
        )
    )
