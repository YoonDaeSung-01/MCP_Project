"""Wiki 테스트용 임시 Vault. 실제 Wiki와 구분되는 개발용 Fixture다."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from learning_app.settings import Settings
from learning_app.wiki_mcp.config import (
    Collection,
    CollectionSpec,
    build_collection_specs,
    build_limits,
)
from learning_app.wiki_mcp.library import WikiLibrary

NOTE_LLM = """---
tags: [AI-IT용어, 핵심]
aliases: [대규모 언어 모델, "Large Language Model"]
status: stable
---

# LLM

대규모 언어 모델의 개요다.

## 개념

토큰을 예측한다. Transformer를 사용한다.

```text
# 코드 안의 줄은 Heading이 아니다
```

## 한계

환각이 생길 수 있다.

### 환각

사실이 아닌 내용을 만든다.

## 개념

같은 이름의 두 번째 Section이다.
"""

NOTE_HASH = """# 02. 해시 · dict와 set

dict는 키로 값을 찾는다. 개수 세기에 쓴다.

## 1. 개념과 원리

set은 존재 여부를 본다.
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    write(root / "ai_terms" / "index.md", "# 용어 색인\n\nLLM 목록\n")
    write(root / "ai_terms" / "위키규칙.md", "# 규칙\n\n포함 대상이 아니다\n")
    write(root / "ai_terms" / "wiki" / "01_원리" / "LLM.md", NOTE_LLM)
    write(root / "ai_terms" / "wiki" / "01_원리" / "Tokenizer.md", "# Tokenizer\n\n문장을 토큰으로 나눈다.\n")
    write(root / "ai_terms" / "raw" / "원본.md", "# 원본\n\n제외 대상\n")
    write(root / "ai_terms" / "wiki" / "_meta" / "메타.md", "# 메타\n\n제외 대상\n")
    write(root / "ai_terms" / "wiki" / ".hidden.md", "# 숨김\n\n제외 대상\n")
    write(root / "ai_terms" / "wiki" / "Backup" / "예전.md", "# 예전\n\n제외 대상\n")
    write(root / "algorithms" / "02_해시_dict_set.md", NOTE_HASH)
    write(root / "algorithms" / "README.md", "# 알고리즘\n\n목록\n")
    write(root / "ai_usage" / "MOC.md", "# AI 활용\n\n비어 있다\n")
    return root


@pytest.fixture
def settings(vault: Path) -> Settings:
    return Settings(
        _env_file=None,
        wiki_root_ai_terms=vault / "ai_terms",
        wiki_root_ai_usage=vault / "ai_usage",
        wiki_root_algorithms=vault / "algorithms",
    )


@pytest.fixture
def specs(settings: Settings) -> dict[Collection, CollectionSpec]:
    return build_collection_specs(settings)


@pytest.fixture
def library(settings: Settings, specs: dict[Collection, CollectionSpec]) -> WikiLibrary:
    lib = WikiLibrary(specs, build_limits(settings))
    lib.refresh()
    return lib


def make_directory_link(link: Path, target: Path) -> bool:
    """Windows Junction 또는 Symlink를 만든다. 만들 수 없으면 False."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        os.symlink(target, link, target_is_directory=True)
        return True
    except OSError:
        return False
