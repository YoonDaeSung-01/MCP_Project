"""Wiki Service.

UI API 및 차후 Agent가 공통으로 호출하는 Wiki 조회 Service 계층.
WikiMCPClient를 통해 stdio 통신으로 Wiki MCP Server와 연동한다.
"""

from __future__ import annotations

from typing import Any

from learning_app.integrations.wiki_mcp_client import WikiMCPClient
from learning_app.wiki_mcp.models import (
    HeadingsResult,
    NoteContent,
    NoteList,
    SearchResult,
)


class WikiService:
    """Wiki 조회를 담당하는 애플리케이션 서비스."""

    def __init__(self, client: WikiMCPClient) -> None:
        self._client = client

    async def list_notes(
        self,
        collection: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> NoteList:
        return await self._client.list_notes(
            collection=collection, cursor=cursor, limit=limit
        )

    async def search_notes(
        self,
        query: str,
        collection: str | None = None,
        limit: int | None = None,
    ) -> SearchResult:
        return await self._client.search_notes(
            query=query, collection=collection, limit=limit
        )

    async def get_headings(self, note_id: str) -> HeadingsResult:
        return await self._client.get_headings(note_id=note_id)

    async def read_note(
        self,
        note_id: str,
        section_id: str | None = None,
        file_version: str | None = None,
        cursor: str | None = None,
    ) -> NoteContent:
        return await self._client.read_note(
            note_id=note_id,
            section_id=section_id,
            file_version=file_version,
            cursor=cursor,
        )

    async def get_index(self) -> dict[str, Any]:
        return await self._client.get_wiki_index()

    async def get_explain_prompt(
        self, topic: str, note_ref: str | None = None
    ) -> str:
        return await self._client.get_explain_prompt(topic=topic, note_ref=note_ref)
