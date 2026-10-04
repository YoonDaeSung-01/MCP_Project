"""FastAPI Wiki API 엔드포인트 테스트."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from learning_app.api.main import app, get_wiki_service
from learning_app.services.wiki_service import WikiService
from learning_app.settings import Settings
from learning_app.wiki_mcp.config import build_collection_specs, build_limits
from learning_app.wiki_mcp.library import WikiLibrary


class InProcessWikiService(WikiService):
    """테스트용 고속 InProcess WikiService (Library 직접 호출)."""

    def __init__(self, library: WikiLibrary) -> None:
        self._library = library

    async def list_notes(self, collection=None, cursor=None, limit=None):
        return self._library.list_notes(collection, cursor, limit)

    async def search_notes(self, query, collection=None, limit=None):
        return self._library.search_notes(query, collection, limit)

    async def get_headings(self, note_id):
        return self._library.get_headings(note_id)

    async def read_note(self, note_id, section_id=None, file_version=None, cursor=None):
        return self._library.read_note(note_id, section_id, file_version, cursor)

    async def get_index(self):
        return self._library.index_status().model_dump(mode="json")


@pytest.fixture
def api_client(library: WikiLibrary) -> TestClient:
    service = InProcessWikiService(library)
    app.dependency_overrides[get_wiki_service] = lambda: service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_api_wiki_notes_list(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/notes?limit=4")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 4
    assert data["next_cursor"] is not None


def test_api_wiki_notes_search(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/notes?query=Transformer")
    assert res.status_code == 200
    data = res.json()
    assert data["total_matches"] == 1
    assert data["hits"][0]["note_id"] == "ai_terms:wiki/01_원리/LLM.md"


def test_api_wiki_headings(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/headings?note_id=ai_terms:wiki/01_원리/LLM.md")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "LLM"
    assert len(data["headings"]) == 5


def test_api_wiki_note_read(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/note?note_id=ai_terms:wiki/01_원리/LLM.md")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "LLM"
    assert "대규모 언어 모델" in data["content"]


def test_api_wiki_index(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/index")
    assert res.status_code == 200
    data = res.json()
    assert "collections" in data
    assert data["complete"] is True


def test_api_wiki_validation_error_returns_400(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/notes?limit=0")
    assert res.status_code == 400
    data = res.json()
    assert data["detail"]["code"] == "validation_error"


def test_api_wiki_not_found_returns_404(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/note?note_id=algorithms:없는문서.md")
    assert res.status_code == 404
    data = res.json()
    assert data["detail"]["code"] == "not_found"


def test_api_wiki_path_traversal_returns_400(api_client: TestClient) -> None:
    res = api_client.get("/api/wiki/note?note_id=algorithms:../secret.md")
    assert res.status_code == 400
    data = res.json()
    assert data["detail"]["code"] == "validation_error"
