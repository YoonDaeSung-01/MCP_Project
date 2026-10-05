"""SQLite 마이그레이션 원자성 및 롤백 회귀 테스트 (B04).

ARCHITECTURE.md §10, §13 준수:
- 마이그레이션 중간 실패 시 일부 Table 변경이 남지 않고 원자적으로 전체 Rollback되는지 검증
- schema_version 기록과 DDL 실행이 단일 트랜잭션으로 커밋/롤백되는지 검증
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from learning_app.db.connection import open_connection
from learning_app.db.migrator import apply_migrations, _split_sql_script


def test_split_sql_script_handles_inline_multiple_statements():
    """한 줄에 있는 복수 SQL 문장을 정확히 분리한다."""
    script = "CREATE TABLE a (id INTEGER); CREATE TABLE b (id INTEGER);"
    statements = _split_sql_script(script)
    assert len(statements) == 2
    assert statements[0] == "CREATE TABLE a (id INTEGER);"
    assert statements[1] == "CREATE TABLE b (id INTEGER);"


def test_split_sql_script_preserves_semicolons_in_strings_comments_and_triggers():
    """문자열 내부, 주석, Trigger 본문의 세미콜론을 문장 경계로 잘못 나누지 않는다."""
    script = """
    -- line comment with ; inside
    /* block comment
    with ; semicolon */
    CREATE TABLE a (id INTEGER, val TEXT);
    INSERT INTO a VALUES (1, 'str;with;semicolons;inside');
    CREATE TRIGGER test_trg AFTER INSERT ON a
    BEGIN
        UPDATE a SET val = 'updated;' WHERE id = new.id;
        DELETE FROM a WHERE id = 999;
    END;
    """
    statements = _split_sql_script(script)
    assert len(statements) == 3
    # 1. CREATE TABLE
    assert "CREATE TABLE a" in statements[0]
    # 2. INSERT INTO (문자열 내 세미콜론 포함)
    assert "INSERT INTO a VALUES" in statements[1]
    assert "'str;with;semicolons;inside'" in statements[1]
    # 3. CREATE TRIGGER (BEGIN...END 내부의 복수 세미콜론 포함 단일 문장)
    assert statements[2].startswith("CREATE TRIGGER test_trg")
    assert statements[2].endswith("END;")
    assert "UPDATE a SET val = 'updated;'" in statements[2]
    assert "DELETE FROM a WHERE id = 999;" in statements[2]


def test_migration_succeeds_with_inline_statements_and_triggers(tmp_path: Path, monkeypatch):
    """한 줄 복수 문장, 문자열 세미콜론, 주석 및 트리거가 포함된 마이그레이션이 정상 실행된다."""
    db_path = tmp_path / "inline_migration_test.sqlite"
    conn = open_connection(db_path)

    test_migrations_dir = tmp_path / "migrations"
    test_migrations_dir.mkdir()

    script = """
    CREATE TABLE a (id INTEGER PRIMARY KEY); CREATE TABLE b (id INTEGER PRIMARY KEY);
    -- comment; with semicolon
    INSERT INTO a VALUES (1);
    CREATE TRIGGER trg_a AFTER INSERT ON a
    BEGIN
        INSERT INTO b VALUES (new.id * 10);
    END;
    """
    (test_migrations_dir / "001_inline.sql").write_text(script, encoding="utf-8")

    import learning_app.db.migrator as migrator_mod
    monkeypatch.setattr(migrator_mod, "MIGRATIONS_DIR", test_migrations_dir)

    # 마이그레이션 실행
    version = apply_migrations(conn)
    assert version == 1

    # 테이블 및 트리거 생성 확인
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'trigger');")
    names = {row[0] for row in cursor.fetchall()}
    assert "a" in names
    assert "b" in names
    assert "trg_a" in names

    # 트리거 동작 확인
    conn.execute("INSERT INTO a VALUES (5);")
    b_rows = conn.execute("SELECT id FROM b WHERE id = 50;").fetchall()
    assert len(b_rows) == 1

    conn.close()


def test_migration_failure_rolls_back_all_partial_tables(tmp_path: Path, monkeypatch):
    """B04: 마이그레이션 SQL 실행 중간에 실패가 발생하면 앞서 생성된 테이블까지 모두 롤백된다."""
    db_path = tmp_path / "migration_test.sqlite"
    conn = open_connection(db_path)

    # 1. 실패를 유발할 테스트용 마이그레이션 디렉터리 준비
    test_migrations_dir = tmp_path / "migrations"
    test_migrations_dir.mkdir()

    # 001: 2개 테이블 생성 후 3번째 문장에서 잘못된 구문(Syntax Error) 발생
    faulty_sql = """
    CREATE TABLE table_one (id INTEGER PRIMARY KEY, title TEXT);
    CREATE TABLE table_two (id INTEGER PRIMARY KEY, value TEXT);
    INVALID_SQL_SYNTAX_CAUSING_FAILURE;
    """
    (test_migrations_dir / "001_faulty.sql").write_text(faulty_sql, encoding="utf-8")

    import learning_app.db.migrator as migrator_mod
    monkeypatch.setattr(migrator_mod, "MIGRATIONS_DIR", test_migrations_dir)

    # 2. 마이그레이션 실행 시도 -> DatabaseError 발생
    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(conn)

    # 3. 검증: table_one, table_two 모두 롤백되어 존재하지 않아야 함
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    assert "table_one" not in tables, "중간 실패한 마이그레이션의 table_one이 롤백되지 않고 남아있다!"
    assert "table_two" not in tables, "중간 실패한 마이그레이션의 table_two가 롤백되지 않고 남아있다!"

    # 4. schema_version에도 1이 기록되지 않고 0이어야 함
    v_cursor = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version;")
    assert v_cursor.fetchone()[0] == 0

    conn.close()


def test_migration_version_insert_failure_rolls_back_tables(tmp_path: Path, monkeypatch):
    """B04: 테이블 생성은 성공했으나 schema_version 기록 중 오류 발생 시 테이블 생성도 함께 롤백된다."""
    db_path = tmp_path / "migration_version_fail.sqlite"
    conn = open_connection(db_path)

    test_migrations_dir = tmp_path / "migrations"
    test_migrations_dir.mkdir()

    valid_sql = "CREATE TABLE safe_table (id INTEGER PRIMARY KEY);"
    (test_migrations_dir / "001_safe.sql").write_text(valid_sql, encoding="utf-8")

    import learning_app.db.migrator as migrator_mod
    monkeypatch.setattr(migrator_mod, "MIGRATIONS_DIR", test_migrations_dir)

    # schema_version 테이블을 읽기 전용 또는 잠긴 상태로 조작하여 버전 기록 시 에러 유발
    # 여기서는 schema_version에 PRIMARY KEY 중복 또는 트리거로 에러 주입
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        );
        """
    )
    # 이미 version 1을 넣어두어 PK 충돌 유발
    conn.execute("INSERT INTO schema_version (version, applied_at) VALUES (1, 'initial');")

    # current_version을 속이기 위해 버전 1이 아닌 버전 1 파일이 실행되도록 강제하는 시나리오
    # 002번 파일인데 schema_version의 트리거로 version 2 삽입을 실패하게 만듦
    (test_migrations_dir / "002_fail_version.sql").write_text(valid_sql, encoding="utf-8")
    conn.execute(
        """
        CREATE TRIGGER block_version_2 BEFORE INSERT ON schema_version
        WHEN NEW.version = 2
        BEGIN
            SELECT RAISE(ABORT, '버전 삽입 강제 실패 주입');
        END;
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        apply_migrations(conn)

    # 검증: safe_table이 롤백되어 없어야 함
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "safe_table" not in tables, "버전 기록 실패 시 safe_table이 롤백되지 않고 남아있다!"

    conn.close()


def test_migration_succeeds_without_trailing_semicolon(tmp_path: Path, monkeypatch):
    """1. 마지막 세미콜론이 없는 정상 SQL도 실제로 적용된다."""
    db_path = tmp_path / "no_trailing_semi.sqlite"
    conn = open_connection(db_path)

    test_migrations_dir = tmp_path / "migrations"
    test_migrations_dir.mkdir()

    # 마지막 문장 'CREATE TABLE table_b (id INTEGER)'에 세미콜론이 없음
    script = "CREATE TABLE table_a (id INTEGER PRIMARY KEY); CREATE TABLE table_b (id INTEGER)"
    (test_migrations_dir / "001_no_semi.sql").write_text(script, encoding="utf-8")

    import learning_app.db.migrator as migrator_mod
    monkeypatch.setattr(migrator_mod, "MIGRATIONS_DIR", test_migrations_dir)

    version = apply_migrations(conn)
    assert version == 1

    # 두 테이블 모두 생성되었는지 확인
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "table_a" in tables
    assert "table_b" in tables

    # schema_version 기록 확인
    v_cursor = conn.execute("SELECT MAX(version) FROM schema_version;")
    assert v_cursor.fetchone()[0] == 1

    conn.close()


def test_migration_trailing_incomplete_sql_rolls_back_all_tables(tmp_path: Path, monkeypatch):
    """2. 마지막 SQL이 미완성이면 앞선 DDL과 schema_version 기록이 모두 Rollback된다."""
    db_path = tmp_path / "incomplete_sql.sqlite"
    conn = open_connection(db_path)

    test_migrations_dir = tmp_path / "migrations"
    test_migrations_dir.mkdir()

    # 첫 번째 문장은 정상이나, 마지막 문장이 괄호가 닫히지 않은 미완성 SQL
    script = "CREATE TABLE table_ok (id INTEGER PRIMARY KEY); CREATE TABLE incomplete_table (id INTEGER"
    (test_migrations_dir / "001_incomplete.sql").write_text(script, encoding="utf-8")

    import learning_app.db.migrator as migrator_mod
    monkeypatch.setattr(migrator_mod, "MIGRATIONS_DIR", test_migrations_dir)

    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(conn)

    # 앞서 생성되었던 table_ok도 롤백되어 없어야 함
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert "table_ok" not in tables, "미완성 SQL 실패 시 앞선 table_ok가 롤백되지 않고 남아있다!"
    assert "incomplete_table" not in tables

    # schema_version에도 기록되지 않아야 함 (0)
    v_cursor = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version;")
    assert v_cursor.fetchone()[0] == 0

    conn.close()
