"""Wiki MCP Client stdio Child Process 통합 테스트.

Backend(Host)가 실제 Child Process로 실행된 Wiki MCP Server와 stdio로 통신하는 경계를 검증한다.
"""

from __future__ import annotations

import pytest

from learning_app.integrations.wiki_mcp_client import WikiMCPClient
from learning_app.settings import Settings


@pytest.mark.asyncio
async def test_client_stdio_process_lifecycle_and_tools(settings: Settings) -> None:
    client = WikiMCPClient(settings=settings)
    assert not client.is_connected

    async with client:
        assert client.is_connected

        # 1. list_notes 호출
        notes = await client.list_notes(limit=3)
        assert len(notes.items) == 3
        first_note_id = notes.items[0].note_id

        # 2. search_notes 호출
        search = await client.search_notes(query="LLM")
        assert search.total_matches >= 1
        llm_hit = next(
            (h for h in search.hits if h.note_id == "ai_terms:wiki/01_원리/LLM.md"), None
        )
        assert llm_hit is not None
        assert llm_hit.title == "LLM"

        # 3. get_headings 호출
        headings = await client.get_headings("ai_terms:wiki/01_원리/LLM.md")
        assert headings.title == "LLM"
        assert len(headings.headings) == 5

        # 4. read_note 호출
        note_content = await client.read_note("ai_terms:wiki/01_원리/LLM.md")
        assert note_content.title == "LLM"
        assert "대규모 언어 모델" in note_content.content
        assert note_content.source_reference.note_id == "ai_terms:wiki/01_원리/LLM.md"

        # 5. Resource wiki://index 조회
        index_data = await client.get_wiki_index()
        assert "collections" in index_data
        assert index_data["complete"] is True

        # 6. Prompt explain_from_wiki 조회
        prompt_text = await client.get_explain_prompt(
            topic="해시", note_ref="algorithms:02_해시_dict_set.md"
        )
        assert "주제: 해시" in prompt_text
        assert "algorithms:02_해시_dict_set.md" in prompt_text

    assert not client.is_connected
