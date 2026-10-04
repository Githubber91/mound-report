"""Tests for the JSON export, against a small synthetic season."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

from pitchlab import db
from pitchlab.export import (
    MIN_PITCHES,
    SCHEMA_VERSION,
    PitcherFile,
    build_pitchers,
    display_name,
    export,
    validate_pitcher,
)
from pitchlab.schema import PITCH_COLUMNS

STARTER = 605483  # throws enough to be exported
MOP_UP = 999001  # a position player with a handful of pitches


def _pitch(
    pitcher: int, name: str, n: int, code: str, velo: float, **extra: object
) -> dict[str, object]:
    row: dict[str, object] = {column: None for column in PITCH_COLUMNS.values()}
    row.update(
        game_id=700000 + n // 50,
        game_date=date(2026, 4, 1) + timedelta(days=n // 50),
        game_type="R",
        at_bat_number=n,
        pitch_number=1,
        pitcher_id=pitcher,
        batter_id=1,
        pitcher_name=name,
        pitcher_hand="L",
        pitch_type=code,
        pitch_name={"FF": "4-Seam Fastball", "SL": "Slider"}.get(code, code),
        velocity_mph=velo,
        spin_rate_rpm=2300.0,
        horizontal_break_ft=0.5,
        induced_vertical_break_ft=1.25,
        description="ball",
    )
    row.update(extra)
    return row


@pytest.fixture
def season_db(tmp_path: Path) -> Path:
    rows: list[dict[str, object]] = []
    for i in range(150):  # 100 fastballs, 50 sliders
        code, velo = ("FF", 96.0) if i < 100 else ("SL", 87.0)
        description = (
            "swinging_strike" if i % 10 == 0 else "foul" if i % 10 == 1 else "ball"
        )
        rows.append(
            _pitch(STARTER, "Snell, Blake", i, code, velo, description=description)
        )
    for i in range(10):
        rows.append(_pitch(MOP_UP, "Utility, Guy", 1000 + i, "FF", 70.0))
    # Spring training and pitchouts must never reach the app.
    rows.append(_pitch(STARTER, "Snell, Blake", 2000, "FF", 99.9, game_type="S"))
    rows.append(_pitch(STARTER, "Snell, Blake", 2001, "PO", 80.0))
    frame = pd.DataFrame(rows)[list(PITCH_COLUMNS.values())]
    path = tmp_path / "season.duckdb"
    with db.connect(path) as connection:
        db.initialise(connection)
        db.upsert_pitches(connection, frame)
    return path


def test_display_name() -> None:
    assert display_name("Snell, Blake") == "Blake Snell"
    assert display_name("Acuña Jr., Ronald") == "Ronald Acuña Jr."
    assert display_name("Ichiro") == "Ichiro"


def test_only_regular_season_pitchers_over_minimum(season_db: Path) -> None:
    with db.connect(season_db) as connection:
        pitchers, through = build_pitchers(connection, 2026)
    assert [p["id"] for p in pitchers] == [STARTER]
    assert pitchers[0]["pitches"] == 150  # spring training and pitchout excluded
    assert pitchers[0]["pitches"] >= MIN_PITCHES
    assert through == "2026-04-21"  # latest regular-season game, any pitcher


def test_arsenal_numbers(season_db: Path) -> None:
    with db.connect(season_db) as connection:
        (pitcher,), _ = build_pitchers(connection, 2026)
    fastball, slider = pitcher["arsenal"]
    assert (fastball["code"], slider["code"]) == ("FF", "SL")  # most-used first
    assert fastball["usage_pct"] == pytest.approx(66.7)
    assert fastball["velocity_mph"] == 96.0
    assert fastball["horizontal_break_in"] == 6.0  # feet converted to inches
    assert fastball["vertical_break_in"] == 15.0
    # 1 in 10 pitches is a whiff and 1 in 10 a foul, so half of swings miss.
    assert fastball["whiff_pct"] == 50.0
    assert set(pitcher["movement"]) == {"FF", "SL"}


def test_validation_catches_impossible_values(season_db: Path) -> None:
    with db.connect(season_db) as connection:
        (pitcher,), _ = build_pitchers(connection, 2026)
    assert validate_pitcher(pitcher) == []
    broken: PitcherFile = json.loads(json.dumps(pitcher))
    broken["arsenal"][0]["velocity_mph"] = 140.0
    assert any("velocity" in problem for problem in validate_pitcher(broken))


def test_export_writes_index_and_pitcher_files(season_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "data"
    export(2026, out, database=season_db)
    index = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert index["schema_version"] == SCHEMA_VERSION
    assert index["pitchers"] == [
        {
            "id": STARTER,
            "name": "Blake Snell",
            "hand": "L",
            "pitches": 150,
            "arsenal": ["FF", "SL"],
        }
    ]
    pitcher = json.loads(
        (out / "pitchers" / f"{STARTER}.json").read_text(encoding="utf-8")
    )
    assert pitcher["name"] == "Blake Snell"


def test_export_refuses_empty_season(season_db: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No regular-season pitches"):
        export(2025, tmp_path / "data", database=season_db)
