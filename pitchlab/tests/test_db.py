"""Tests for storage, against a throwaway database in a temp directory."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pitchlab import db
from pitchlab.ingest import normalise


def test_initialise_is_repeatable(tmp_path: Path) -> None:
    with db.connect(tmp_path / "test.duckdb") as connection:
        db.initialise(connection)
        db.initialise(connection)
        assert db.count_pitches(connection) == 0


def test_round_trip(tmp_path: Path, raw_statcast: pd.DataFrame) -> None:
    frame = normalise(raw_statcast)
    with db.connect(tmp_path / "test.duckdb") as connection:
        db.initialise(connection)
        assert db.upsert_pitches(connection, frame) == 2
        assert db.stored_date_range(connection) == ("2024-07-01", "2024-07-01")


def test_date_range_is_none_when_empty(tmp_path: Path) -> None:
    with db.connect(tmp_path / "test.duckdb") as connection:
        db.initialise(connection)
        assert db.stored_date_range(connection) is None


def test_reingest_does_not_duplicate(tmp_path: Path, raw_statcast: pd.DataFrame) -> None:
    """Running the same dates twice must leave the table as one run would."""
    frame = normalise(raw_statcast)
    with db.connect(tmp_path / "test.duckdb") as connection:
        db.initialise(connection)
        db.upsert_pitches(connection, frame)
        assert db.upsert_pitches(connection, frame) == 2


def test_reingest_replaces_corrected_values(
    tmp_path: Path, raw_statcast: pd.DataFrame
) -> None:
    """Statcast sometimes revises a pitch; the newer value wins."""
    with db.connect(tmp_path / "test.duckdb") as connection:
        db.initialise(connection)
        db.upsert_pitches(connection, normalise(raw_statcast))
        revised = raw_statcast.copy()
        revised.loc[0, "release_speed"] = 96.4
        db.upsert_pitches(connection, normalise(revised))
        row = connection.execute(
            "SELECT velocity_mph FROM pitches WHERE pitch_type = 'FF'"
        ).fetchone()
        assert row is not None
        assert row[0] == 96.4
