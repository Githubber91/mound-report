"""Tests for the normalisation step.

We test `normalise` rather than `fetch`, because `fetch` talks to the
internet and a test that needs the internet is a test that will fail for
reasons unrelated to your code.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from pitchlab.ingest import date_chunks, normalise, season_window


def test_renames_columns_to_our_names(raw_statcast: pd.DataFrame) -> None:
    frame = normalise(raw_statcast)
    assert "velocity_mph" in frame.columns
    assert "release_speed" not in frame.columns
    # Statcast calls the pitcher `player_name`, which is a trap.
    assert frame.loc[0, "pitcher_name"] == "Snell, Blake"


def test_parses_dates(raw_statcast: pd.DataFrame) -> None:
    frame = normalise(raw_statcast)
    assert frame.loc[0, "game_date"] == date(2024, 7, 1)


def test_drops_rows_without_identifiers(raw_statcast: pd.DataFrame) -> None:
    broken = raw_statcast.copy()
    broken.loc[0, "pitcher"] = None
    frame = normalise(broken)
    assert len(frame) == 1


def test_rejects_unexpected_shape(raw_statcast: pd.DataFrame) -> None:
    """If Statcast changes its schema, fail loudly instead of guessing."""
    with pytest.raises(ValueError, match="missing columns"):
        normalise(raw_statcast.drop(columns=["release_speed"]))


def test_keeps_movement_and_handedness(raw_statcast: pd.DataFrame) -> None:
    frame = normalise(raw_statcast)
    assert frame.loc[0, "horizontal_break_ft"] == 0.55
    assert frame.loc[0, "induced_vertical_break_ft"] == 1.42
    assert frame.loc[0, "pitcher_hand"] == "L"
    assert frame.loc[0, "pitch_name"] == "4-Seam Fastball"


def test_drops_duplicate_pitches_within_a_download(raw_statcast: pd.DataFrame) -> None:
    doubled = pd.concat([raw_statcast, raw_statcast.iloc[[0]]], ignore_index=True)
    assert len(normalise(doubled)) == 2


def test_date_chunks_cover_range_without_overlap() -> None:
    chunks = list(date_chunks(date(2026, 4, 1), date(2026, 4, 16), days=7))
    assert chunks == [
        (date(2026, 4, 1), date(2026, 4, 7)),
        (date(2026, 4, 8), date(2026, 4, 14)),
        (date(2026, 4, 15), date(2026, 4, 16)),
    ]


def test_date_chunks_reject_backwards_range() -> None:
    with pytest.raises(ValueError, match="precedes"):
        list(date_chunks(date(2026, 4, 2), date(2026, 4, 1)))


def test_season_window_is_capped_at_today() -> None:
    start, end = season_window(2026, today=date(2026, 10, 4))
    assert start == date(2026, 2, 15)
    assert end == date(2026, 10, 4)


def test_season_window_rejects_future_season() -> None:
    with pytest.raises(ValueError, match="not started"):
        season_window(2027, today=date(2026, 10, 4))
