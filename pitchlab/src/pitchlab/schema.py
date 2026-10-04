"""The shape of a pitch.

Statcast returns ~90 columns of varying quality. We select a deliberate
subset and name it, rather than passing an anonymous DataFrame around.
A named schema is the thing that makes the rest of the project legible --
to you in six months, and to a model reading the code.
"""

from typing import Final

# Column name in Statcast -> column name we store.
# Statcast's own names are inconsistent (`player_name` is the *pitcher*),
# so we rename at the boundary and never think about it again.
PITCH_COLUMNS: Final[dict[str, str]] = {
    "game_pk": "game_id",
    "game_date": "game_date",
    "game_type": "game_type",
    "at_bat_number": "at_bat_number",
    "pitch_number": "pitch_number",
    "pitcher": "pitcher_id",
    "batter": "batter_id",
    "player_name": "pitcher_name",
    "p_throws": "pitcher_hand",
    "pitch_type": "pitch_type",
    "pitch_name": "pitch_name",
    "release_speed": "velocity_mph",
    "release_spin_rate": "spin_rate_rpm",
    "release_extension": "extension_ft",
    "pfx_x": "horizontal_break_ft",
    "pfx_z": "induced_vertical_break_ft",
    "plate_x": "plate_x_ft",
    "plate_z": "plate_z_ft",
    "sz_top": "strike_zone_top_ft",
    "sz_bot": "strike_zone_bottom_ft",
    "balls": "balls",
    "strikes": "strikes",
    "outs_when_up": "outs",
    "inning": "inning",
    "description": "description",
    "events": "event",
    "launch_speed": "exit_velocity_mph",
    "launch_angle": "launch_angle_deg",
    "estimated_woba_using_speedangle": "expected_woba",
    "home_team": "home_team",
    "away_team": "away_team",
}

# A pitch is uniquely identified by its game, plate appearance and position
# in that plate appearance. Used to make re-running an ingest safe.
PITCH_KEY: Final[tuple[str, ...]] = ("game_id", "at_bat_number", "pitch_number")

CREATE_PITCHES_TABLE: Final[str] = """
CREATE TABLE IF NOT EXISTS pitches (
    game_id                   BIGINT   NOT NULL,
    game_date                 DATE     NOT NULL,
    game_type                 VARCHAR,
    at_bat_number             INTEGER  NOT NULL,
    pitch_number              INTEGER  NOT NULL,
    pitcher_id                BIGINT   NOT NULL,
    batter_id                 BIGINT   NOT NULL,
    pitcher_name              VARCHAR,
    pitcher_hand              VARCHAR,
    pitch_type                VARCHAR,
    pitch_name                VARCHAR,
    velocity_mph              DOUBLE,
    spin_rate_rpm             DOUBLE,
    extension_ft              DOUBLE,
    horizontal_break_ft       DOUBLE,
    induced_vertical_break_ft DOUBLE,
    plate_x_ft                DOUBLE,
    plate_z_ft                DOUBLE,
    strike_zone_top_ft        DOUBLE,
    strike_zone_bottom_ft     DOUBLE,
    balls                     INTEGER,
    strikes                   INTEGER,
    outs                      INTEGER,
    inning                    INTEGER,
    description               VARCHAR,
    event                     VARCHAR,
    exit_velocity_mph         DOUBLE,
    launch_angle_deg          DOUBLE,
    expected_woba             DOUBLE,
    home_team                 VARCHAR,
    away_team                 VARCHAR,
    PRIMARY KEY (game_id, at_bat_number, pitch_number)
);
"""
