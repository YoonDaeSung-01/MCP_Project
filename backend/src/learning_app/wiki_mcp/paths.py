"""Note ID 검증과 허용 Root 안의 File 확인. Path Traversal, Junction과 Symlink 우회를 막는다."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

from learning_app.wiki_mcp.config import (
    EXCLUDED_NAMES,
    NOTE_SUFFIX,
    Collection,
    CollectionSpec,
)
from learning_app.wiki_mcp.errors import WikiError, WikiErrorCode

MAX_NOTE_ID_LENGTH = 512
FILE_VERSION_LENGTH = 16
NOTE_ID_SEPARATOR = ":"

# Windows 예약 Device 이름. File 이름의 첫 점 앞부분으로 비교한다.
_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)
_INVALID_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')


def is_excluded_name(name: str) -> bool:
    """숨김 이름과 제외 Directory 이름인지 확인한다."""
    return name.startswith(".") or name.casefold() in EXCLUDED_NAMES


def make_note_id(collection: Collection, parts: tuple[str, ...]) -> str:
    return f"{collection.value}{NOTE_ID_SEPARATOR}{'/'.join(parts)}"


def parse_note_id(note_id: str) -> tuple[Collection, tuple[str, ...]]:
    """Note ID를 Collection과 정규화한 상대 경로 요소로 나눈다.

    형식 검사만 한다. File 존재와 Root 안의 위치는 resolve_note_file에서 확인한다.
    """
    if not isinstance(note_id, str) or not note_id or len(note_id) > MAX_NOTE_ID_LENGTH:
        raise WikiError(WikiErrorCode.VALIDATION_ERROR, "note_id 형식이 올바르지 않다")
    collection_text, separator, relative = note_id.partition(NOTE_ID_SEPARATOR)
    if not separator:
        raise WikiError(
            WikiErrorCode.VALIDATION_ERROR,
            "note_id는 '<collection>:<상대 경로>' 형식이어야 한다",
        )
    try:
        collection = Collection(collection_text)
    except ValueError:
        raise WikiError(
            WikiErrorCode.VALIDATION_ERROR,
            f"알 수 없는 collection이다: {collection_text}",
        ) from None
    return collection, _validate_relative(relative)


def _validate_relative(relative: str) -> tuple[str, ...]:
    if not relative or "\\" in relative or relative.startswith("/"):
        raise WikiError(WikiErrorCode.VALIDATION_ERROR, "note_id의 상대 경로가 올바르지 않다")
    parts = tuple(unicodedata.normalize("NFC", part) for part in relative.split("/"))
    for part in parts:
        if part in ("", ".", ".."):
            raise WikiError(
                WikiErrorCode.VALIDATION_ERROR, "상대 경로에 빈 요소, '.', '..'를 쓸 수 없다"
            )
        if _INVALID_CHARS.search(part) or part != part.rstrip(" ."):
            raise WikiError(
                WikiErrorCode.VALIDATION_ERROR, "경로 요소에 사용할 수 없는 문자가 있다"
            )
        if part.split(".")[0].upper() in _RESERVED_NAMES:
            raise WikiError(WikiErrorCode.VALIDATION_ERROR, "예약된 이름은 사용할 수 없다")
    if not parts[-1].casefold().endswith(NOTE_SUFFIX):
        raise WikiError(WikiErrorCode.VALIDATION_ERROR, f"{NOTE_SUFFIX} File만 읽을 수 있다")
    if any(is_excluded_name(part) for part in parts):
        raise WikiError(WikiErrorCode.PERMISSION_DENIED, "제외 대상 경로다")
    return parts


def resolve_note_file(spec: CollectionSpec, parts: tuple[str, ...]) -> Path:
    """검증한 상대 경로를 실제 File로 바꾼다. 최종 경로가 허용 Root 밖이면 거부한다.

    Path.resolve는 Junction과 Symlink를 따라간 실제 경로를 반환한다.
    실제 경로가 Root 밖이거나 요청한 경로와 다르면 읽지 않는다.
    """
    note_label = make_note_id(spec.collection, parts)
    if spec.root is None:
        raise WikiError(WikiErrorCode.NOT_FOUND, f"{spec.collection.value} Root가 설정되지 않았다")
    if not spec.allows(parts):
        raise WikiError(WikiErrorCode.PERMISSION_DENIED, f"제외 대상 경로다: {note_label}")
    try:
        root_real = spec.root.resolve(strict=True)
    except FileNotFoundError:
        raise WikiError(
            WikiErrorCode.NOT_FOUND, f"{spec.collection.value} Root를 찾을 수 없다"
        ) from None
    except OSError:
        raise WikiError(
            WikiErrorCode.READ_ERROR, f"{spec.collection.value} Root를 열 수 없다"
        ) from None
    if not root_real.is_dir():
        raise WikiError(WikiErrorCode.NOT_FOUND, f"{spec.collection.value} Root가 Directory가 아니다")

    try:
        real = root_real.joinpath(*parts).resolve(strict=True)
    except (FileNotFoundError, NotADirectoryError):
        raise WikiError(WikiErrorCode.NOT_FOUND, f"Note를 찾을 수 없다: {note_label}") from None
    except (OSError, RuntimeError):
        raise WikiError(WikiErrorCode.READ_ERROR, f"Note 경로를 확인할 수 없다: {note_label}") from None

    if not real.is_relative_to(root_real):
        raise WikiError(WikiErrorCode.PERMISSION_DENIED, f"허용 Root 밖의 경로다: {note_label}")
    canonical = tuple(unicodedata.normalize("NFC", p) for p in real.relative_to(root_real).parts)
    if canonical != parts:
        # 대소문자, 8.3 짧은 이름, 내부 Link로 같은 File을 다른 ID로 읽는 일을 막는다.
        raise WikiError(
            WikiErrorCode.NOT_FOUND, f"note_id가 실제 경로와 일치하지 않는다: {note_label}"
        )
    if not real.is_file():
        raise WikiError(WikiErrorCode.NOT_FOUND, f"Note를 찾을 수 없다: {note_label}")
    return real


def read_source(path: Path, note_id: str, max_bytes: int) -> tuple[str, str]:
    """File을 읽어 (줄바꿈을 정규화한 본문, file_version)을 반환한다.

    file_version은 원본 Byte의 SHA-256 앞 FILE_VERSION_LENGTH자리다.
    """
    try:
        if path.stat().st_size > max_bytes:
            raise WikiError(WikiErrorCode.READ_ERROR, f"File이 너무 크다: {note_id}")
        data = path.read_bytes()
    except FileNotFoundError:
        raise WikiError(WikiErrorCode.NOT_FOUND, f"Note를 찾을 수 없다: {note_id}") from None
    except OSError:
        raise WikiError(WikiErrorCode.READ_ERROR, f"Note를 읽을 수 없다: {note_id}") from None
    if len(data) > max_bytes:
        raise WikiError(WikiErrorCode.READ_ERROR, f"File이 너무 크다: {note_id}")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise WikiError(WikiErrorCode.READ_ERROR, f"UTF-8로 읽을 수 없다: {note_id}") from None
    version = hashlib.sha256(data).hexdigest()[:FILE_VERSION_LENGTH]
    return text.replace("\r\n", "\n").replace("\r", "\n"), version
