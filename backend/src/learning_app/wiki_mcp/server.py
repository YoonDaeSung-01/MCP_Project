"""읽기 전용 Wiki MCP Server.

stdio로 Backend의 MCP Client와 통신한다.
stdout은 MCP 통신에만 사용하고 일반 로그는 stderr로 보낸다.
Protocol Handshake는 공식 mcp SDK에 위임한다.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp.server import MCPServer

from learning_app.settings import Settings, get_settings
from learning_app.wiki_mcp.config import build_collection_specs, build_limits
from learning_app.wiki_mcp.library import WikiLibrary
from learning_app.wiki_mcp.models import (
    HeadingsResult,
    NoteContent,
    NoteList,
    SearchResult,
)

logger = logging.getLogger("learning_app.wiki_mcp")


def _setup_logging() -> None:
    """stdout을 오염시키지 않도록 모든 로그 핸들러를 stderr로 설정한다."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    # 기존 핸들러 제거 후 stderr 핸들러만 등록
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def create_wiki_server(
    library: WikiLibrary | None = None,
    settings: Settings | None = None,
) -> MCPServer:
    """Wiki MCP Server 인스턴스를 생성하고 Tool, Resource, Prompt를 등록한다."""
    _setup_logging()

    if library is None:
        cfg = settings or get_settings()
        specs = build_collection_specs(cfg)
        limits = build_limits(cfg)
        library = WikiLibrary(specs, limits)
        library.refresh()

    server = MCPServer(
        name="wiki-mcp",
        version="0.1.0",
        instructions="기존 Markdown Wiki 자료를 읽기 전용으로 탐색하고 조회하는 MCP Server",
    )

    # ---------------------------------------------------------------- Tools

    @server.tool(
        name="list_notes",
        description="Collection 안의 Note 목록을 조회한다. pagination cursor를 지원한다.",
    )
    def list_notes(
        collection: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        result: NoteList = library.list_notes(
            collection=collection, cursor=cursor, limit=limit
        )
        return result.model_dump(mode="json")

    @server.tool(
        name="search_notes",
        description="Keyword로 Wiki Note를 검색한다. 제목과 Alias 일치가 본문보다 우선한다.",
    )
    def search_notes(
        query: str,
        collection: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        result: SearchResult = library.search_notes(
            query=query, collection=collection, limit=limit
        )
        return result.model_dump(mode="json")

    @server.tool(
        name="get_headings",
        description="Note의 Heading 목차와 Section ID, 줄 번호, file_version을 조회한다.",
    )
    def get_headings(note_id: str) -> dict[str, Any]:
        result: HeadingsResult = library.get_headings(note_id=note_id)
        return result.model_dump(mode="json")

    @server.tool(
        name="read_note",
        description="Note 전체 또는 특정 Section 원문을 읽는다. file_version 불일치 시 source_changed를 반환한다.",
    )
    def read_note(
        note_id: str,
        section_id: str | None = None,
        file_version: str | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        result: NoteContent = library.read_note(
            note_id=note_id,
            section_id=section_id,
            file_version=file_version,
            cursor=cursor,
        )
        return result.model_dump(mode="json")

    # ---------------------------------------------------------------- Resources

    @server.resource(
        uri="wiki://index",
        name="Wiki Index",
        description="Wiki Collection 구성과 색인 메타데이터를 제공한다.",
        mime_type="application/json",
    )
    def get_wiki_index() -> str:
        status = library.index_status()
        return json.dumps(status.model_dump(mode="json"), ensure_ascii=False, indent=2)

    # ---------------------------------------------------------------- Prompts

    @server.prompt(
        name="explain_from_wiki",
        description="Wiki 자료를 근거로 개념을 설명할 때 사용하는 지침 템플릿",
    )
    def explain_from_wiki(topic: str, note_ref: str | None = None) -> str:
        note_guide = (
            f"참조할 Note ID: {note_ref}\n해당 Note의 Heading과 내용을 먼저 확인하고 설명에 반영하십시오."
            if note_ref
            else "관련 Wiki Note를 search_notes로 먼저 검색하고, 확인된 Section 근거를 바탕으로 설명하십시오."
        )
        return (
            f"주제: {topic}\n"
            f"{note_guide}\n"
            "지침:\n"
            "1. 반드시 읽은 Wiki Note의 실제 Section을 근거로 제시하십시오.\n"
            "2. 답변 끝에 Source Reference (Note ID, Section ID, 줄 번호)를 명시하십시오.\n"
            "3. Wiki에 없는 내용을 임의로 추측하지 마십시오."
        )

    return server


def main() -> None:
    """CLI 엔트리포인트. stdio transport로 MCP Server를 실행한다."""
    server = create_wiki_server()
    logger.info("Wiki MCP Server starting on stdio transport...")
    server.run("stdio")


if __name__ == "__main__":
    main()
