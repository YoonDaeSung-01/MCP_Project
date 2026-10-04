"""Wiki MCP Client.

stdio를 통해 별도 Child Process로 실행되는 Wiki MCP Server와 통신한다.
Backend(Host) 안에서 단일 프로세스 생명주기와 ClientSession을 관리한다.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent

from learning_app.settings import Settings, get_settings
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode
from learning_app.wiki_mcp.models import (
    HeadingsResult,
    NoteContent,
    NoteList,
    SearchResult,
)

logger = logging.getLogger(__name__)


class WikiMCPClient:
    """Wiki MCP Server Child Process와 연결하는 비동기 Client."""

    def __init__(
        self,
        settings: Settings | None = None,
        cwd: Path | None = None,
        python_executable: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._cwd = cwd or Path(__file__).resolve().parents[3]  # backend 디렉터리
        self._python_executable = python_executable or sys.executable

        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    async def connect(self) -> None:
        """Wiki MCP Server Child Process를 시작하고 세션을 초기화한다."""
        async with self._lock:
            if self._session is not None:
                return

            env = dict(os.environ)
            # Backend .env 경로와 Python 환경 설정 전달
            env["PYTHONUNBUFFERED"] = "1"
            if self._settings.wiki_root_ai_terms:
                env["WIKI_ROOT_AI_TERMS"] = str(self._settings.wiki_root_ai_terms)
            if self._settings.wiki_root_ai_usage:
                env["WIKI_ROOT_AI_USAGE"] = str(self._settings.wiki_root_ai_usage)
            if self._settings.wiki_root_algorithms:
                env["WIKI_ROOT_ALGORITHMS"] = str(self._settings.wiki_root_algorithms)

            params = StdioServerParameters(
                command=self._python_executable,
                args=["-m", "learning_app.wiki_mcp.server"],
                env=env,
                cwd=str(self._cwd),
            )

            stack = AsyncExitStack()
            try:
                read_stream, write_stream = await stack.enter_async_context(
                    stdio_client(params)
                )
                session = await stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()
                self._session = session
                self._exit_stack = stack
                logger.info("Connected to Wiki MCP Server process via stdio")
            except Exception as exc:
                await stack.aclose()
                logger.error("Failed to connect to Wiki MCP Server: %s", exc)
                raise WikiError(
                    WikiErrorCode.READ_ERROR,
                    f"Wiki MCP Server에 연결할 수 없다: {exc}",
                ) from exc

    async def close(self) -> None:
        """세션과 Child Process를 안전하게 종료한다."""
        async with self._lock:
            if self._exit_stack is not None:
                await self._exit_stack.aclose()
                self._exit_stack = None
                self._session = None
                logger.info("Disconnected from Wiki MCP Server")

    async def __aenter__(self) -> WikiMCPClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _ensure_connected(self) -> ClientSession:
        if self._session is None:
            await self.connect()
        assert self._session is not None
        return self._session

    async def _call_tool_json(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Tool을 호출하고 JSON 결과를 dict로 파싱한다."""
        session = await self._ensure_connected()
        async with self._lock:
            res = await session.call_tool(name=name, arguments=arguments)

        if res.is_error:
            error_msg = (
                res.content[0].text
                if res.content and isinstance(res.content[0], TextContent)
                else "Unknown MCP error"
            )
            raise WikiError(WikiErrorCode.READ_ERROR, f"MCP Tool 오류: {error_msg}")

        if not res.content or not isinstance(res.content[0], TextContent):
            raise WikiError(WikiErrorCode.READ_ERROR, "MCP 응답에 내용이 없다")

        try:
            data = json.loads(res.content[0].text)
        except json.JSONDecodeError as exc:
            raise WikiError(
                WikiErrorCode.READ_ERROR, "MCP 응답 JSON 해석에 실패했다"
            ) from exc

        return data

    # ---------------------------------------------------------------- Tool API

    async def list_notes(
        self,
        collection: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> NoteList:
        args: dict[str, Any] = {}
        if collection is not None:
            args["collection"] = collection
        if cursor is not None:
            args["cursor"] = cursor
        if limit is not None:
            args["limit"] = limit

        data = await self._call_tool_json("list_notes", args)
        return NoteList.model_validate(data)

    async def search_notes(
        self,
        query: str,
        collection: str | None = None,
        limit: int | None = None,
    ) -> SearchResult:
        args: dict[str, Any] = {"query": query}
        if collection is not None:
            args["collection"] = collection
        if limit is not None:
            args["limit"] = limit

        data = await self._call_tool_json("search_notes", args)
        return SearchResult.model_validate(data)

    async def get_headings(self, note_id: str) -> HeadingsResult:
        data = await self._call_tool_json("get_headings", {"note_id": note_id})
        return HeadingsResult.model_validate(data)

    async def read_note(
        self,
        note_id: str,
        section_id: str | None = None,
        file_version: str | None = None,
        cursor: str | None = None,
    ) -> NoteContent:
        args: dict[str, Any] = {"note_id": note_id}
        if section_id is not None:
            args["section_id"] = section_id
        if file_version is not None:
            args["file_version"] = file_version
        if cursor is not None:
            args["cursor"] = cursor

        data = await self._call_tool_json("read_note", args)
        return NoteContent.model_validate(data)

    # ---------------------------------------------------------------- Resource API

    async def get_wiki_index(self) -> dict[str, Any]:
        """wiki://index Resource를 조회한다."""
        session = await self._ensure_connected()
        async with self._lock:
            res = await session.read_resource("wiki://index")

        if not res.contents:
            raise WikiError(WikiErrorCode.NOT_FOUND, "wiki://index 자원이 비어 있다")

        first_content = res.contents[0]
        # TextResourceContents의 text 필드 읽기
        text = getattr(first_content, "text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise WikiError(
                WikiErrorCode.READ_ERROR, "Resource JSON 해석 실패"
            ) from exc

    # ---------------------------------------------------------------- Prompt API

    async def get_explain_prompt(
        self, topic: str, note_ref: str | None = None
    ) -> str:
        """explain_from_wiki Prompt를 조회한다."""
        session = await self._ensure_connected()
        args: dict[str, Any] = {"topic": topic}
        if note_ref is not None:
            args["note_ref"] = note_ref

        async with self._lock:
            res = await session.get_prompt("explain_from_wiki", arguments=args)

        messages = getattr(res, "messages", [])
        if not messages:
            return ""
        # 첫 번째 메시지의 내용 추출
        content = getattr(messages[0], "content", None)
        if isinstance(content, TextContent):
            return content.text
        if isinstance(content, str):
            return content
        return str(content)
