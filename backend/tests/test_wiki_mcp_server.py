"""Wiki MCP Server 단위 테스트.

MCPServer에 등록된 Tool, Resource, Prompt의 직접 호출 계약을 검증한다.
"""

from __future__ import annotations

import json
import pytest

from learning_app.wiki_mcp.library import WikiLibrary
from learning_app.wiki_mcp.server import create_wiki_server


@pytest.mark.asyncio
async def test_server_tools_registered_and_callable(library: WikiLibrary) -> None:
    server = create_wiki_server(library=library)

    # 1. list_notes 호출
    list_res = await server.call_tool("list_notes", {"limit": 5})
    assert not list_res.is_error
    data = json.loads(list_res.content[0].text)
    assert len(data["items"]) == 5
    assert data["items"][0]["note_id"].startswith("ai_terms:")

    # 2. search_notes 호출
    search_res = await server.call_tool("search_notes", {"query": "Transformer"})
    assert not search_res.is_error
    search_data = json.loads(search_res.content[0].text)
    assert search_data["total_matches"] == 1
    assert search_data["hits"][0]["note_id"] == "ai_terms:wiki/01_원리/LLM.md"

    # 3. get_headings 호출
    headings_res = await server.call_tool(
        "get_headings", {"note_id": "ai_terms:wiki/01_원리/LLM.md"}
    )
    assert not headings_res.is_error
    headings_data = json.loads(headings_res.content[0].text)
    assert headings_data["title"] == "LLM"
    assert len(headings_data["headings"]) == 5

    # 4. read_note 호출
    read_res = await server.call_tool(
        "read_note", {"note_id": "ai_terms:wiki/01_원리/LLM.md"}
    )
    assert not read_res.is_error
    read_data = json.loads(read_res.content[0].text)
    assert read_data["title"] == "LLM"
    assert "대규모 언어 모델" in read_data["content"]


@pytest.mark.asyncio
async def test_server_resource_wiki_index(library: WikiLibrary) -> None:
    server = create_wiki_server(library=library)
    res = await server.read_resource("wiki://index")
    assert res
    first = res[0]
    content_text = getattr(first, "content", getattr(first, "text", ""))
    data = json.loads(content_text)
    assert "collections" in data
    assert data["complete"] is True


@pytest.mark.asyncio
async def test_server_prompt_explain_from_wiki(library: WikiLibrary) -> None:
    server = create_wiki_server(library=library)
    res = await server.get_prompt(
        "explain_from_wiki",
        arguments={"topic": "LLM 동작 원리", "note_ref": "ai_terms:wiki/01_원리/LLM.md"},
    )
    assert res.messages
    prompt_text = res.messages[0].content.text
    assert "주제: LLM 동작 원리" in prompt_text
    assert "참조할 Note ID: ai_terms:wiki/01_원리/LLM.md" in prompt_text
    assert "Source Reference" in prompt_text
