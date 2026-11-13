import sqlite3
from pathlib import Path

from storage.database import Database


def test_sqlite_database_initialization(tmp_path: Path):
    path = tmp_path / "nested" / "agent.sqlite3"

    Database(path).initialize()

    with sqlite3.connect(path) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='applications'"
        ).fetchall()
    assert tables == [("applications",)]
