"""Backend 설정. 환경 변수와 backend/.env에서 읽는다.

비밀값은 이 Module에 선언하지 않는다.
Wiki MCP Process가 Model API Key를 읽지 않도록 필요한 항목만 둔다.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Wiki 연결과 조회 제한 설정."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    wiki_root_ai_terms: Path | None = None
    wiki_root_ai_usage: Path | None = None
    wiki_root_algorithms: Path | None = None

    wiki_search_default_limit: int = Field(default=10, ge=1)
    wiki_search_max_limit: int = Field(default=20, ge=1)
    wiki_read_max_chars: int = Field(default=12000, ge=1)
    wiki_snippet_max_chars: int = Field(default=200, ge=20)
    wiki_snippets_per_note: int = Field(default=3, ge=1)
    wiki_max_file_bytes: int = Field(default=2_000_000, ge=1)


@lru_cache
def get_settings() -> Settings:
    """프로세스 안에서 한 번만 설정을 읽는다."""
    return Settings()
