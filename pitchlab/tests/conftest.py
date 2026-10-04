"""Shared test fixtures."""

from __future__ import annotations

import pandas as pd
import pytest

from pitchlab.schema import PITCH_COLUMNS


@pytest.fixture
def raw_statcast() -> pd.DataFrame:
    """Two rows shaped like a real Statcast response.

    Using a fixture rather than a live download means the tests are fast,
    deterministic, and work on a plane.
    """
    rows = [
        {
            "game_pk": 745000,
            "game_date": "2024-07-01",
            "game_type": "R",
            "at_bat_number": 14,
            "pitch_number": 4,
            "pitcher": 605483,
            "batter": 665742,
            "player_name": "Snell, Blake",
            "p_throws": "L",
            "pitch_type": "FF",
            "pitch_name": "4-Seam Fastball",
            "release_speed": 96.1,
            "release_spin_rate": 2310.0,
            "release_extension": 6.6,
            "pfx_x": 0.55,
            "pfx_z": 1.42,
            "plate_x": -0.21,
            "plate_z": 2.64,
            "sz_top": 3.38,
            "sz_bot": 1.55,
            "balls": 1,
            "strikes": 2,
            "outs_when_up": 1,
            "inning": 3,
            "description": "swinging_strike",
            "events": "strikeout",
            "launch_speed": None,
            "launch_angle": None,
            "estimated_woba_using_speedangle": None,
            "home_team": "SF",
            "away_team": "LAD",
        },
        {
            "game_pk": 745000,
            "game_date": "2024-07-01",
            "game_type": "R",
            "at_bat_number": 15,
            "pitch_number": 2,
            "pitcher": 605483,
            "batter": 665742,
            "player_name": "Snell, Blake",
            "p_throws": "L",
            "pitch_type": "SL",
            "pitch_name": "Slider",
            "release_speed": 87.4,
            "release_spin_rate": 2585.0,
            "release_extension": 6.4,
            "pfx_x": -0.31,
            "pfx_z": 0.12,
            "plate_x": 0.44,
            "plate_z": 1.92,
            "sz_top": 3.38,
            "sz_bot": 1.55,
            "balls": 0,
            "strikes": 1,
            "outs_when_up": 1,
            "inning": 3,
            "description": "hit_into_play",
            "events": "single",
            "launch_speed": 101.3,
            "launch_angle": 12.0,
            "estimated_woba_using_speedangle": 0.612,
            "home_team": "SF",
            "away_team": "LAD",
        },
    ]
    frame = pd.DataFrame(rows)
    assert set(PITCH_COLUMNS).issubset(frame.columns)
    return frame
