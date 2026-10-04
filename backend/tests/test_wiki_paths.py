"""Note ID 검증과 Root 경계 테스트. Path Traversal, Junction과 제외 대상을 확인한다."""

from pathlib import Path

import pytest

from learning_app.wiki_mcp.config import Collection, CollectionSpec
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode
from learning_app.wiki_mcp.library import WikiLibrary
from learning_app.wiki_mcp.paths import parse_note_id, resolve_note_file

from .conftest import make_directory_link, write


def code_of(excinfo: pytest.ExceptionInfo[WikiError]) -> WikiErrorCode:
    return excinfo.value.code


@pytest.mark.parametrize(
    "note_id",
    [
        "",
        "no-separator.md",
        "unknown:a.md",
        "algorithms:",
        "algorithms:../secret.md",
        "algorithms:a/../../secret.md",
        "algorithms:/abs.md",
        "algorithms:a\\b.md",
        "algorithms:C:/x.md",
        "algorithms:a.md:stream",
        "algorithms:dir//a.md",
        "algorithms:./a.md",
        "algorithms:note.txt",
        "algorithms:note.md.",
        "algorithms:CON.md",
        "algorithms:a/nul.md",
        "algorithms:a?.md",
    ],
)
def test_invalid_note_id_is_validation_error(note_id: str) -> None:
    with pytest.raises(WikiError) as excinfo:
        parse_note_id(note_id)
    assert code_of(excinfo) is WikiErrorCode.VALIDATION_ERROR


@pytest.mark.parametrize(
    "note_id",
    ["ai_terms:raw/a.md", "ai_terms:wiki/_meta/a.md", "algorithms:.hidden.md", "ai_terms:wiki/Backup/a.md"],
)
def test_excluded_names_are_permission_denied(note_id: str) -> None:
    with pytest.raises(WikiError) as excinfo:
        parse_note_id(note_id)
    assert code_of(excinfo) is WikiErrorCode.PERMISSION_DENIED


def test_note_id_is_nfc_normalized() -> None:
    nfd = "algorithms:" + "02_해시".encode("utf-8").decode("utf-8")
    import unicodedata

    decomposed = unicodedata.normalize("NFD", nfd) + ".md"
    _, parts = parse_note_id(decomposed)
    assert parts == (unicodedata.normalize("NFC", "02_해시.md"),)


def test_ai_terms_outside_include_is_permission_denied(
    specs: dict[Collection, CollectionSpec],
) -> None:
    with pytest.raises(WikiError) as excinfo:
        resolve_note_file(specs[Collection.AI_TERMS], ("위키규칙.md",))
    assert code_of(excinfo) is WikiErrorCode.PERMISSION_DENIED


def test_missing_file_is_not_found(specs: dict[Collection, CollectionSpec]) -> None:
    with pytest.raises(WikiError) as excinfo:
        resolve_note_file(specs[Collection.ALGORITHMS], ("없는파일.md",))
    assert code_of(excinfo) is WikiErrorCode.NOT_FOUND


def test_case_mismatch_is_not_found_not_alias(specs: dict[Collection, CollectionSpec]) -> None:
    with pytest.raises(WikiError) as excinfo:
        resolve_note_file(specs[Collection.ALGORITHMS], ("readme.md",))
    assert code_of(excinfo) is WikiErrorCode.NOT_FOUND


def test_unconfigured_root_is_not_found() -> None:
    spec = CollectionSpec(Collection.ALGORITHMS, root=None)
    with pytest.raises(WikiError) as excinfo:
        resolve_note_file(spec, ("a.md",))
    assert code_of(excinfo) is WikiErrorCode.NOT_FOUND


def test_junction_to_outside_root_is_denied_and_not_listed(
    vault: Path, library: WikiLibrary
) -> None:
    outside = vault.parent / "outside"
    write(outside / "secret.md", "# 비밀\n\nRoot 밖의 자료\n")
    link = vault / "algorithms" / "link"
    if not make_directory_link(link, outside):
        pytest.skip("이 환경에서는 Junction 또는 Symlink를 만들 수 없다")

    with pytest.raises(WikiError) as excinfo:
        library.read_note("algorithms:link/secret.md")
    assert code_of(excinfo) is WikiErrorCode.PERMISSION_DENIED

    library.refresh()
    ids = [item.note_id for item in library.list_notes("algorithms", limit=20).items]
    assert not any(note_id.startswith("algorithms:link/") for note_id in ids)
    assert library.search_notes("Root 밖의 자료").total_matches == 0


def test_junction_inside_root_pointing_to_excluded_dir_is_not_readable(
    vault: Path, library: WikiLibrary
) -> None:
    link = vault / "ai_terms" / "wiki" / "shortcut"
    if not make_directory_link(link, vault / "ai_terms" / "raw"):
        pytest.skip("이 환경에서는 Junction 또는 Symlink를 만들 수 없다")
    with pytest.raises(WikiError) as excinfo:
        library.read_note("ai_terms:wiki/shortcut/원본.md")
    assert code_of(excinfo) is WikiErrorCode.NOT_FOUND


def test_error_messages_do_not_expose_absolute_paths(vault: Path, library: WikiLibrary) -> None:
    with pytest.raises(WikiError) as excinfo:
        library.read_note("algorithms:없는파일.md")
    assert str(vault) not in str(excinfo.value)
