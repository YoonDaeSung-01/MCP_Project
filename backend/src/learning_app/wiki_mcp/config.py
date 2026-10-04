"""Wiki Collection 정의와 조회 제한."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from learning_app.settings import Settings


class Collection(StrEnum):
    AI_TERMS = "ai_terms"
    AI_USAGE = "ai_usage"
    ALGORITHMS = "algorithms"


# ARCHITECTURE §7: AI-IT용어는 wiki와 index.md만 대상으로 한다.
# None은 Root 전체를 뜻한다.
COLLECTION_INCLUDES: Mapping[Collection, tuple[str, ...] | None] = {
    Collection.AI_TERMS: ("wiki", "index.md"),
    Collection.AI_USAGE: None,
    Collection.ALGORITHMS: None,
}

# ARCHITECTURE §7: raw, _meta, Backup과 숨김 File은 제외한다. 이름은 casefold로 비교한다.
EXCLUDED_NAMES = frozenset({"raw", "_meta", "backup", "backups"})

NOTE_SUFFIX = ".md"


@dataclass(frozen=True)
class CollectionSpec:
    """Collection 하나의 Root와 포함 규칙."""

    collection: Collection
    root: Path | None
    includes: tuple[str, ...] | None = None

    def allows(self, parts: Sequence[str]) -> bool:
        """상대 경로의 첫 요소가 포함 대상인지 확인한다."""
        if self.includes is None:
            return True
        return bool(parts) and parts[0] in self.includes


@dataclass(frozen=True)
class WikiLimits:
    """조회 제한. Settings의 값으로 만든다."""

    default_limit: int
    max_limit: int
    read_max_chars: int
    snippet_max_chars: int
    snippets_per_note: int
    max_file_bytes: int


def build_collection_specs(settings: Settings) -> dict[Collection, CollectionSpec]:
    """Settings의 Root 설정으로 Collection 규칙을 만든다. Root 미설정은 root=None이다."""
    return {
        collection: CollectionSpec(
            collection=collection,
            root=getattr(settings, f"wiki_root_{collection.value}"),
            includes=COLLECTION_INCLUDES[collection],
        )
        for collection in Collection
    }


def build_limits(settings: Settings) -> WikiLimits:
    return WikiLimits(
        default_limit=settings.wiki_search_default_limit,
        max_limit=settings.wiki_search_max_limit,
        read_max_chars=settings.wiki_read_max_chars,
        snippet_max_chars=settings.wiki_snippet_max_chars,
        snippets_per_note=settings.wiki_snippets_per_note,
        max_file_bytes=settings.wiki_max_file_bytes,
    )
