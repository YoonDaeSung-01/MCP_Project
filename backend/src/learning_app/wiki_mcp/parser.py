"""Markdown 분석. Frontmatter, Heading과 Section 범위를 구한다.

Heading 분석은 markdown-it-py의 Token을 사용한다.
Code Fence 안의 문자열은 Heading으로 분석하지 않는다.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

import yaml
from markdown_it import MarkdownIt

SECTION_ID_PREFIX = "s"
FRONTMATTER_DELIMITER = "---"
FRONTMATTER_END = (FRONTMATTER_DELIMITER, "...")

_MARKDOWN = MarkdownIt("commonmark")


@dataclass(frozen=True)
class Heading:
    """Heading 하나와 그 Section의 줄 범위. 줄은 1부터 시작하고 끝 줄을 포함한다."""

    section_id: str
    level: int
    title: str
    path: tuple[str, ...]
    start_line: int
    end_line: int


@dataclass(frozen=True)
class ParsedNote:
    title: str
    aliases: tuple[str, ...]
    tags: tuple[str, ...]
    status: str | None
    headings: tuple[Heading, ...]
    body_start: int  # 본문 첫 줄의 0 기준 위치. Frontmatter가 없으면 0이다.
    warnings: tuple[str, ...]


def normalize_text(value: str) -> str:
    """검색용 정규화. Unicode 호환 형태 통일과 대소문자 무시."""
    return unicodedata.normalize("NFKC", value).casefold()


def split_lines(text: str) -> list[str]:
    """줄바꿈이 정규화된 본문을 줄 목록으로 나눈다. 마지막 개행의 빈 줄은 만들지 않는다."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def parse_note(lines: list[str], fallback_title: str) -> ParsedNote:
    body_start, frontmatter, warning = _split_frontmatter(lines)
    warnings = (warning,) if warning else ()

    # Frontmatter 줄을 빈 줄로 바꿔 줄 번호를 보존한다.
    source = "\n".join([""] * body_start + lines[body_start:])
    raw_headings: list[tuple[int, str, int]] = []
    tokens = _MARKDOWN.parse(source)
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.level != 0 or not token.map:
            continue
        text = tokens[index + 1].content.strip()
        if text:
            raw_headings.append((int(token.tag[1:]), text, token.map[0] + 1))

    headings = _build_sections(raw_headings, total_lines=len(lines))
    return ParsedNote(
        title=_pick_title(frontmatter, headings, fallback_title),
        aliases=_as_str_tuple(frontmatter.get("aliases", frontmatter.get("alias"))),
        tags=tuple(tag.lstrip("#") for tag in _as_str_tuple(frontmatter.get("tags"))),
        status=_as_optional_str(frontmatter.get("status")),
        headings=headings,
        body_start=body_start,
        warnings=warnings,
    )


def _split_frontmatter(lines: list[str]) -> tuple[int, dict[str, object], str | None]:
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return 0, {}, None
    for index in range(1, len(lines)):
        if lines[index].rstrip() not in FRONTMATTER_END:
            continue
        try:
            data = yaml.safe_load("\n".join(lines[1:index]))
        except yaml.YAMLError:
            return index + 1, {}, "Frontmatter YAML을 해석하지 못했다. 본문만 분석한다"
        return index + 1, data if isinstance(data, dict) else {}, None
    return 0, {}, None


def _build_sections(
    raw: list[tuple[int, str, int]], total_lines: int
) -> tuple[Heading, ...]:
    headings: list[Heading] = []
    stack: list[tuple[int, str]] = []
    for index, (level, title, start) in enumerate(raw):
        end = total_lines
        for next_level, _, next_start in raw[index + 1 :]:
            if next_level <= level:
                end = next_start - 1
                break
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        headings.append(
            Heading(
                section_id=f"{SECTION_ID_PREFIX}{index + 1}",
                level=level,
                title=title,
                path=tuple(item[1] for item in stack),
                start_line=start,
                end_line=max(end, start),
            )
        )
    return tuple(headings)


def _pick_title(
    frontmatter: dict[str, object], headings: tuple[Heading, ...], fallback: str
) -> str:
    title = frontmatter.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    for heading in headings:
        if heading.level == 1:
            return heading.title
    return fallback


def _as_str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    items = value if isinstance(value, list) else str(value).split(",")
    return tuple(text for item in items if (text := str(item).strip()))


def _as_optional_str(value: object) -> str | None:
    return str(value).strip() or None if value is not None else None
