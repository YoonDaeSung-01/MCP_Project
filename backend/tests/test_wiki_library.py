"""WikiLibrary 테스트. 목록, 검색, Heading 조회, 본문 읽기와 오류 구분을 확인한다."""

import unicodedata
from pathlib import Path

import pytest

from learning_app.settings import Settings
from learning_app.wiki_mcp.config import (
    Collection,
    CollectionSpec,
    build_collection_specs,
    build_limits,
)
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode
from learning_app.wiki_mcp.library import WikiLibrary
from learning_app.wiki_mcp.models import CollectionState

from .conftest import NOTE_LLM, write

LLM_ID = "ai_terms:wiki/01_원리/LLM.md"


def error_code(callable_, *args, **kwargs) -> WikiErrorCode:
    with pytest.raises(WikiError) as excinfo:
        callable_(*args, **kwargs)
    return excinfo.value.code


# ---------------------------------------------------------------- 목록과 Index


def test_index_contains_only_allowed_notes(library: WikiLibrary) -> None:
    ids = [i.note_id for i in library.list_notes(limit=20).items]
    assert ids == [
        "ai_terms:index.md",
        "ai_terms:wiki/01_원리/LLM.md",
        "ai_terms:wiki/01_원리/Tokenizer.md",
        "ai_usage:MOC.md",
        "algorithms:02_해시_dict_set.md",
        "algorithms:README.md",
    ]
    assert library.index_status().complete


def test_list_note_summary_fields(library: WikiLibrary) -> None:
    item = next(i for i in library.list_notes("ai_terms", limit=20).items if i.note_id == LLM_ID)
    assert item.title == "LLM"
    assert item.aliases == ["대규모 언어 모델", "Large Language Model"]
    assert item.tags == ["AI-IT용어", "핵심"]
    assert item.status == "stable"
    assert len(item.file_version) == 16


def test_list_pagination_cursor(library: WikiLibrary) -> None:
    first = library.list_notes(limit=4)
    assert len(first.items) == 4 and first.next_cursor
    second = library.list_notes(cursor=first.next_cursor, limit=4)
    assert len(second.items) == 2 and second.next_cursor is None
    assert {i.note_id for i in first.items}.isdisjoint(i.note_id for i in second.items)


def test_list_cursor_after_refresh_is_source_changed(library: WikiLibrary) -> None:
    cursor = library.list_notes(limit=2).next_cursor
    library.refresh()
    assert error_code(library.list_notes, cursor=cursor) is WikiErrorCode.SOURCE_CHANGED


def test_bad_cursor_and_collection_are_validation_errors(library: WikiLibrary) -> None:
    assert error_code(library.list_notes, cursor="abc") is WikiErrorCode.VALIDATION_ERROR
    assert error_code(library.list_notes, collection="nope") is WikiErrorCode.VALIDATION_ERROR
    assert error_code(library.list_notes, limit=0) is WikiErrorCode.VALIDATION_ERROR


# ---------------------------------------------------------------- 검색


def test_title_beats_alias_beats_tag_beats_body(vault: Path, settings: Settings) -> None:
    write(vault / "algorithms" / "a_본문.md", "# 다른 제목\n\n검색어토큰이 본문에 있다\n")
    write(vault / "algorithms" / "b_태그.md", "---\ntags: [검색어토큰]\n---\n# 태그 제목\n")
    write(vault / "algorithms" / "c_별칭.md", "---\naliases: [검색어토큰 별칭]\n---\n# 별칭 제목\n")
    write(vault / "algorithms" / "d_제목.md", "# 검색어토큰 안내\n")
    write(vault / "algorithms" / "e_정확.md", "# 검색어토큰\n")
    library = WikiLibrary(build_collection_specs(settings), build_limits(settings))
    library.refresh()

    result = library.search_notes("검색어토큰", "algorithms")
    assert [h.matched_in for h in result.hits] == ["title_exact", "title", "alias", "tag", "body"]
    assert [h.rank for h in result.hits] == [1, 2, 3, 4, 5]
    assert result.hits[0].note_id == "algorithms:e_정확.md"


def test_same_rank_is_ordered_by_note_id(vault: Path, settings: Settings) -> None:
    write(vault / "algorithms" / "z.md", "# z\n\n공통어가 있다\n")
    write(vault / "algorithms" / "b.md", "# b\n\n공통어가 있다\n")
    library = WikiLibrary(build_collection_specs(settings), build_limits(settings))
    library.refresh()
    ids = [h.note_id for h in library.search_notes("공통어", "algorithms").hits]
    assert ids == ["algorithms:b.md", "algorithms:z.md"]


def test_alias_exact_match_found_with_korean_and_case(library: WikiLibrary) -> None:
    korean = library.search_notes("대규모 언어 모델")
    assert korean.hits[0].note_id == LLM_ID
    assert korean.hits[0].matched_in == "alias_exact"
    assert library.search_notes("large language model").hits[0].note_id == LLM_ID


def test_unicode_normalization_nfd_query_matches(library: WikiLibrary) -> None:
    query = unicodedata.normalize("NFD", "해시")
    assert library.search_notes(query).hits[0].note_id == "algorithms:02_해시_dict_set.md"


def test_multiple_terms_must_all_match(library: WikiLibrary) -> None:
    assert library.search_notes("토큰 환각").total_matches == 1
    assert library.search_notes("토큰 존재하지않는단어").total_matches == 0


def test_snippet_has_source_reference_pointing_to_real_line(library: WikiLibrary) -> None:
    hit = library.search_notes("Transformer", "ai_terms").hits[0]
    snippet = hit.snippets[0]
    ref = snippet.source_reference
    assert snippet.heading_path == ["LLM", "개념"]
    assert ref.note_id == LLM_ID and ref.section_id is not None
    content = library.read_note(LLM_ID, file_version=ref.file_version)
    assert "Transformer" in content.content.split("\n")[ref.start_line - 1]


def test_frontmatter_lines_are_not_snippets(library: WikiLibrary) -> None:
    hit = library.search_notes("핵심", "ai_terms").hits[0]
    assert hit.matched_in == "tag"
    assert hit.snippets == []


def test_empty_result_is_complete_and_has_no_warning(library: WikiLibrary) -> None:
    result = library.search_notes("전혀없는검색어qqq")
    assert result.hits == [] and result.total_matches == 0
    assert result.complete and result.warnings == []


def test_limit_is_clamped_and_reported(library: WikiLibrary) -> None:
    assert library.search_notes("a", limit=999).applied_limit == build_limits(Settings(_env_file=None)).max_limit
    assert error_code(library.search_notes, "   ") is WikiErrorCode.VALIDATION_ERROR
    assert error_code(library.search_notes, "x", limit=0) is WikiErrorCode.VALIDATION_ERROR


def test_unavailable_collection_is_not_reported_as_empty_result(
    vault: Path, settings: Settings, specs: dict[Collection, CollectionSpec]
) -> None:
    broken = dict(specs)
    broken[Collection.ALGORITHMS] = CollectionSpec(Collection.ALGORITHMS, root=vault / "없는폴더")
    broken[Collection.AI_USAGE] = CollectionSpec(Collection.AI_USAGE, root=None)
    library = WikiLibrary(broken, build_limits(settings))
    status = library.refresh()

    states = {c.collection: c.state for c in status.collections}
    assert states["algorithms"] is CollectionState.UNAVAILABLE
    assert states["ai_usage"] is CollectionState.UNAVAILABLE
    assert states["ai_terms"] is CollectionState.OK

    result = library.search_notes("해시")
    assert result.hits == []
    assert not result.complete and result.warnings
    only_ok = library.search_notes("해시", "ai_terms")
    assert only_ok.complete and only_ok.warnings == []


def test_unreadable_file_makes_collection_partial(vault: Path, settings: Settings) -> None:
    (vault / "algorithms" / "깨짐.md").write_bytes(b"\xff\xfe\x00 not utf-8 \x80")
    library = WikiLibrary(build_collection_specs(settings), build_limits(settings))
    status = library.refresh()
    algorithms = next(c for c in status.collections if c.collection == "algorithms")
    assert algorithms.state is CollectionState.PARTIAL
    assert algorithms.failed_count == 1
    assert algorithms.failed_examples == ["algorithms:깨짐.md"]
    assert not library.search_notes("해시").complete


def test_ai_terms_without_wiki_directory_is_unavailable(tmp_path: Path, settings: Settings) -> None:
    root = tmp_path / "empty_terms"
    root.mkdir()
    write(root / "위키규칙.md", "# 규칙\n")
    specs = build_collection_specs(Settings(_env_file=None, wiki_root_ai_terms=root))
    library = WikiLibrary(specs, build_limits(settings))
    status = library.refresh()
    terms = next(c for c in status.collections if c.collection == "ai_terms")
    assert terms.state is CollectionState.UNAVAILABLE


# ---------------------------------------------------------------- 읽기


def test_get_headings(library: WikiLibrary) -> None:
    result = library.get_headings(LLM_ID)
    assert result.title == "LLM"
    assert [h.title for h in result.headings] == ["LLM", "개념", "한계", "환각", "개념"]
    assert result.headings[2].path == ["LLM", "한계"]
    assert len(result.file_version) == 16


def test_read_whole_note_and_section(library: WikiLibrary) -> None:
    whole = library.read_note(LLM_ID)
    assert whole.section is None and whole.start_line == 1
    assert whole.content.startswith("---\n")
    assert whole.next_cursor is None

    headings = library.get_headings(LLM_ID).headings
    section = library.read_note(LLM_ID, section_id=headings[2].section_id)
    assert section.content.startswith("## 한계")
    assert "사실이 아닌 내용" in section.content
    assert "두 번째 Section" not in section.content
    assert section.source_reference.section_id == headings[2].section_id
    assert section.start_line == headings[2].start_line


def test_chunked_read_reassembles_original(vault: Path, settings: Settings) -> None:
    long_note = "# 긴 문서\n\n" + "\n".join(f"{n}번째 줄 " + "가" * 30 for n in range(1, 60)) + "\n"
    write(vault / "algorithms" / "긴문서.md", long_note)
    limited = Settings(
        _env_file=None,
        wiki_root_algorithms=vault / "algorithms",
        wiki_read_max_chars=200,
    )
    library = WikiLibrary(build_collection_specs(limited), build_limits(limited))
    library.refresh()

    note_id = "algorithms:긴문서.md"
    parts, cursor, expected_line, guard = [], None, 1, 0
    while True:
        chunk = library.read_note(note_id, cursor=cursor)
        assert len(chunk.content) <= 200
        assert chunk.start_line == expected_line
        parts.append(chunk.content)
        expected_line = chunk.end_line + 1
        cursor = chunk.next_cursor
        guard += 1
        assert guard < 100
        if cursor is None:
            break
    assert len(parts) > 3
    assert "".join(parts) == long_note.rstrip("\n")


def test_file_version_mismatch_is_source_changed(vault: Path, library: WikiLibrary) -> None:
    old_version = library.get_headings(LLM_ID).file_version
    write(vault / "ai_terms" / "wiki" / "01_원리" / "LLM.md", NOTE_LLM + "\n## 추가\n\n내용\n")
    assert (
        error_code(library.read_note, LLM_ID, file_version=old_version)
        is WikiErrorCode.SOURCE_CHANGED
    )
    refreshed = library.get_headings(LLM_ID)
    assert refreshed.file_version != old_version
    assert refreshed.headings[-1].title == "추가"
    assert library.read_note(LLM_ID, file_version=refreshed.file_version).title == "LLM"


def test_read_cursor_with_old_version_is_source_changed(vault: Path, settings: Settings) -> None:
    write(vault / "algorithms" / "긴문서.md", "# 제목\n\n" + "\n".join("가" * 50 for _ in range(30)))
    limited = Settings(_env_file=None, wiki_root_algorithms=vault / "algorithms", wiki_read_max_chars=100)
    library = WikiLibrary(build_collection_specs(limited), build_limits(limited))
    cursor = library.read_note("algorithms:긴문서.md").next_cursor
    assert cursor
    write(vault / "algorithms" / "긴문서.md", "# 제목\n\n바뀐 내용\n")
    assert error_code(library.read_note, "algorithms:긴문서.md", cursor=cursor) is WikiErrorCode.SOURCE_CHANGED


def test_read_error_codes(library: WikiLibrary) -> None:
    assert error_code(library.read_note, LLM_ID, section_id="s999") is WikiErrorCode.NOT_FOUND
    assert error_code(library.read_note, LLM_ID, section_id="abc") is WikiErrorCode.VALIDATION_ERROR
    assert error_code(library.read_note, LLM_ID, cursor="bad") is WikiErrorCode.VALIDATION_ERROR
    assert error_code(library.read_note, "algorithms:없음.md") is WikiErrorCode.NOT_FOUND
    assert error_code(library.read_note, "algorithms:../x.md") is WikiErrorCode.VALIDATION_ERROR


def test_read_note_not_in_index_but_valid_is_readable(vault: Path, library: WikiLibrary) -> None:
    write(vault / "algorithms" / "새문서.md", "# 새 문서\n\n본문\n")
    assert library.read_note("algorithms:새문서.md").title == "새 문서"
    assert library.search_notes("새 문서", "algorithms").total_matches == 0
    library.refresh()
    assert library.search_notes("새 문서", "algorithms").total_matches == 1


def test_crlf_and_bom_are_handled(vault: Path, settings: Settings) -> None:
    (vault / "algorithms" / "crlf.md").write_bytes("\ufeff# 윈도우 문서\r\n\r\n## 절\r\n\r\n내용\r\n".encode("utf-8"))
    library = WikiLibrary(build_collection_specs(settings), build_limits(settings))
    result = library.get_headings("algorithms:crlf.md")
    assert result.title == "윈도우 문서"
    assert [h.start_line for h in result.headings] == [1, 3]
    assert "\r" not in library.read_note("algorithms:crlf.md").content
