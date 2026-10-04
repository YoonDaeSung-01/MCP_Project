"""FastAPI application entrypoint and Wiki API routes."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from learning_app.integrations.wiki_mcp_client import WikiMCPClient
from learning_app.services.wiki_service import WikiService
from learning_app.settings import get_settings
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode

_wiki_client: WikiMCPClient | None = None
_wiki_service: WikiService | None = None


def get_wiki_service() -> WikiService:
    """WikiService 인스턴스를 반환한다 (FastAPI Dependency)."""
    global _wiki_service, _wiki_client
    if _wiki_service is None:
        if _wiki_client is None:
            _wiki_client = WikiMCPClient(get_settings())
        _wiki_service = WikiService(_wiki_client)
    return _wiki_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 종료 시 활성화된 Wiki MCP Client를 닫는다."""
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


def _handle_wiki_error(exc: WikiError) -> HTTPException:
    status_map = {
        WikiErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        WikiErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        WikiErrorCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
        WikiErrorCode.SOURCE_CHANGED: status.HTTP_409_CONFLICT,
        WikiErrorCode.READ_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    status_code = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=status_code,
        detail={"code": exc.code.value, "message": exc.message},
    )


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/wiki/notes")
async def get_wiki_notes(
    query: str | None = Query(default=None, description="검색어"),
    collection: str | None = Query(default=None, description="Collection 식별자"),
    cursor: str | None = Query(default=None, description="Pagination 커서"),
    limit: int | None = Query(default=None, description="최대 조회 개수"),
    service: Annotated[WikiService, Depends(get_wiki_service)] = None,  # type: ignore
) -> dict[str, Any]:
    """Wiki Note 목록 조회 또는 검색."""
    try:
        if query:
            res = await service.search_notes(
                query=query, collection=collection, limit=limit
            )
            return res.model_dump(mode="json")
        res = await service.list_notes(
            collection=collection, cursor=cursor, limit=limit
        )
        return res.model_dump(mode="json")
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc


@app.get("/api/wiki/headings")
async def get_wiki_headings(
    note_id: str = Query(..., description="Note ID 식별자"),
    service: Annotated[WikiService, Depends(get_wiki_service)] = None,  # type: ignore
) -> dict[str, Any]:
    """Note의 목차와 Heading 정보 조회."""
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
    """Note 전체 또는 Section 원문 조회."""
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
    """Wiki 인덱스 구성 및 메타데이터 조회."""
    try:
        return await service.get_index()
    except WikiError as exc:
        raise _handle_wiki_error(exc) from exc
