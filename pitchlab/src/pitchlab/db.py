"""Database access. DuckDB is a single file on disk that speaks SQL fast.

No server to run, no Docker, no credentials -- and the same SQL you write
here is the SQL a sports analytics job will ask you about.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb
import pandas as pd

from pitchlab.config import DATABASE_PATH
from pitchlab.schema import CREATE_PITCHES_TABLE, PITCH_KEY


@contextmanager
def connect(path: Path | None = None) -> Iterator[duckdb.DuckDBPyConnection]:
    """Open the database, guaranteeing it is closed again.

    Using a context manager means a crash mid-ingest cannot leave a
    half-open file handle behind.
    """
    target = path if path is not None else DATABASE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(target))
    try:
        yield connection
    finally:
        connection.close()


def initialise(connection: duckdb.DuckDBPyConnection) -> None:
    """Create tables if they do not exist. Safe to call repeatedly."""
    connection.execute(CREATE_PITCHES_TABLE)


def count_pitches(connection: duckdb.DuckDBPyConnection) -> int:
    """How many pitches are currently stored."""
    row = connection.execute("SELECT count(*) FROM pitches").fetchone()
    if row is None:
        return 0
    return int(row[0])


def stored_date_range(
    connection: duckdb.DuckDBPyConnection,
) -> tuple[str, str] | None:
    """The first and last game dates held, or None when the table is empty."""
    row = connection.execute(
        "SELECT min(game_date), max(game_date) FROM pitches"
    ).fetchone()
    if row is None or row[0] is None:
        return None
    return (str(row[0]), str(row[1]))


def upsert_pitches(connection: duckdb.DuckDBPyConnection, frame: pd.DataFrame) -> int:
    """Insert pitches, replacing any with the same key. Returns the new total.

    Delete-then-insert inside one transaction: simple, and a re-run of the
    same dates leaves the table exactly as one run would.
    """
    columns = ", ".join(frame.columns)
    key = ", ".join(PITCH_KEY)
    connection.register("incoming", frame)
    try:
        connection.execute("BEGIN TRANSACTION")
        connection.execute(
            f"DELETE FROM pitches WHERE ({key}) IN (SELECT {key} FROM incoming)"
        )
        connection.execute(
            f"INSERT INTO pitches ({columns}) SELECT {columns} FROM incoming"
        )
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.unregister("incoming")
    return count_pitches(connection)
