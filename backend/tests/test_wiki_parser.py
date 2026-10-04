"""Markdown 분석 테스트."""

from learning_app.wiki_mcp.parser import parse_note, split_lines

from .conftest import NOTE_LLM


def parse(text: str, fallback: str = "fallback"):
    return parse_note(split_lines(text), fallback)


def test_frontmatter_fields_and_h1_title() -> None:
    note = parse(NOTE_LLM)
    assert note.title == "LLM"
    assert note.aliases == ("대규모 언어 모델", "Large Language Model")
    assert note.tags == ("AI-IT용어", "핵심")
    assert note.status == "stable"
    assert note.warnings == ()


def test_title_priority_frontmatter_then_h1_then_file_name() -> None:
    assert parse("---\ntitle: 지정 제목\n---\n# H1\n").title == "지정 제목"
    assert parse("# H1만 있다\n").title == "H1만 있다"
    assert parse("본문만 있다\n", fallback="파일이름").title == "파일이름"


def test_code_fence_heading_is_ignored() -> None:
    note = parse(NOTE_LLM)
    titles = [h.title for h in note.headings]
    assert "코드 안의 줄은 Heading이 아니다" not in " ".join(titles)
    assert titles == ["LLM", "개념", "한계", "환각", "개념"]


def test_same_heading_name_is_distinguished_by_section_id_and_line() -> None:
    note = parse(NOTE_LLM)
    first, second = [h for h in note.headings if h.title == "개념"]
    assert first.section_id != second.section_id
    assert first.start_line < second.start_line


def test_section_range_includes_subsections_and_matches_real_lines() -> None:
    text = NOTE_LLM
    lines = split_lines(text)
    note = parse(text)
    limit = next(h for h in note.headings if h.title == "한계")
    sub = next(h for h in note.headings if h.title == "환각")
    assert limit.path == ("LLM", "한계")
    assert sub.path == ("LLM", "한계", "환각")
    assert lines[limit.start_line - 1] == "## 한계"
    assert lines[sub.start_line - 1] == "### 환각"
    # 한계 Section은 하위 환각을 포함하고, 다음 같은 수준 Heading 앞에서 끝난다.
    assert limit.end_line >= sub.end_line
    assert lines[limit.end_line] == "## 개념"


def test_invalid_frontmatter_yaml_keeps_body_and_reports_warning() -> None:
    note = parse("---\ntags: [깨짐\n---\n# 제목\n\n본문\n")
    assert note.title == "제목"
    assert note.warnings
    assert note.headings[0].start_line == 4


def test_unclosed_frontmatter_is_not_treated_as_frontmatter() -> None:
    note = parse("---\n# 제목\n본문\n")
    assert note.body_start == 0
    assert note.headings[0].title == "제목"


def test_heading_lines_are_preserved_after_frontmatter() -> None:
    note = parse("---\ntags: [a]\n---\n\n# 제목\n")
    assert note.headings[0].start_line == 5
