"""Turn the pitch database into the small JSON files the app reads.

Run it with:

    python -m pitchlab.export --season 2026 --out ../public/data

Writes:

    index.json              every pitcher, for search, plus metadata
    pitchers/<id>.json      one pitcher's arsenal and movement sample

The app has no server, so everything it shows is computed here, once.
Every file is checked by `validate_*` before it is written: bad numbers
stop the export instead of reaching users.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from datetime import date
from pathlib import Path
from typing import Any, Final, TypedDict

import duckdb

from pitchlab import db

logger = logging.getLogger(__name__)

# Bump when the JSON shape changes, so an old app never misreads new data.
SCHEMA_VERSION: Final[int] = 1

# Fewer pitches than this is mostly position players pitching in blowouts.
MIN_PITCHES: Final[int] = 100

# A pitch type thrown fewer times than this is noise, not part of an arsenal.
MIN_PITCHES_PER_TYPE: Final[int] = 5

# Points per pitch type for the movement chart. Enough to show the shape of
# the cloud without making each file large.
SAMPLE_PER_TYPE: Final[int] = 60

# Not real pitch types: pitchouts, unknowns, and Statcast's catch-all.
EXCLUDED_PITCH_TYPES: Final[tuple[str, ...]] = ("PO", "UN", "FA")

# Swing and miss definitions, following Baseball Savant's conventions.
SWINGS: Final[tuple[str, ...]] = (
    "swinging_strike",
    "swinging_strike_blocked",
    "foul",
    "foul_tip",
    "foul_bunt",
    "missed_bunt",
    "bunt_foul_tip",
    "hit_into_play",
)
WHIFFS: Final[tuple[str, ...]] = (
    "swinging_strike",
    "swinging_strike_blocked",
    "missed_bunt",
)

# Sanity limits. Anything outside these is a data error, not a fact.
VELOCITY_RANGE: Final[tuple[float, float]] = (35.0, 106.0)
SPIN_RANGE: Final[tuple[float, float]] = (0.0, 4000.0)
BREAK_RANGE_IN: Final[tuple[float, float]] = (-36.0, 36.0)


class PitchSummary(TypedDict):
    code: str
    name: str
    count: int
    usage_pct: float
    velocity_mph: float
    max_velocity_mph: float
    spin_rpm: float | None
    horizontal_break_in: float
    vertical_break_in: float
    whiff_pct: float | None


class PitcherFile(TypedDict):
    schema_version: int
    id: int
    name: str
    hand: str
    season: int
    pitches: int
    through: str
    arsenal: list[PitchSummary]
    movement: dict[str, list[list[float]]]


class IndexEntry(TypedDict):
    id: int
    name: str
    hand: str
    pitches: int
    arsenal: list[str]


class IndexFile(TypedDict):
    schema_version: int
    data_version: str
    season: int
    through: str
    source: str
    pitchers: list[IndexEntry]


def display_name(statcast_name: str) -> str:
    """Statcast writes 'Last, First'; people read 'First Last'.

    'Acuña Jr., Ronald' becomes 'Ronald Acuña Jr.'.
    """
    last, sep, first = statcast_name.partition(", ")
    if not sep:
        return statcast_name.strip()
    return f"{first.strip()} {last.strip()}"


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def _season_filter(season: int) -> str:
    excluded = _in_list(EXCLUDED_PITCH_TYPES)
    return (
        f"game_type = 'R' AND year(game_date) = {int(season)} "
        f"AND pitch_type IS NOT NULL AND pitch_type NOT IN ({excluded}) "
        "AND velocity_mph IS NOT NULL"
    )


def build_pitchers(
    connection: duckdb.DuckDBPyConnection, season: int
) -> tuple[list[PitcherFile], str]:
    """Aggregate one regular season into per-pitcher summaries.

    Returns the pitcher files and the last game date included.
    """
    where = _season_filter(season)

    through_row = connection.execute(
        f"SELECT max(game_date) FROM pitches WHERE {where}"
    ).fetchone()
    if through_row is None or through_row[0] is None:
        raise ValueError(f"No regular-season pitches stored for {season}")
    through = str(through_row[0])

    pitchers = connection.execute(
        f"""
        SELECT pitcher_id, any_value(pitcher_name) AS name,
               mode(pitcher_hand) AS hand, count(*) AS pitches
        FROM pitches WHERE {where}
        GROUP BY pitcher_id
        HAVING count(*) >= {MIN_PITCHES}
        ORDER BY pitcher_id
        """
    ).fetchall()

    arsenal_rows = connection.execute(
        f"""
        SELECT pitcher_id, pitch_type, any_value(pitch_name) AS pitch_name,
               count(*) AS n,
               avg(velocity_mph) AS velo, max(velocity_mph) AS max_velo,
               avg(spin_rate_rpm) AS spin,
               avg(horizontal_break_ft) * 12 AS hb_in,
               avg(induced_vertical_break_ft) * 12 AS ivb_in,
               count(*) FILTER (WHERE description IN ({_in_list(SWINGS)})) AS swings,
               count(*) FILTER (WHERE description IN ({_in_list(WHIFFS)})) AS whiffs
        FROM pitches WHERE {where}
        GROUP BY pitcher_id, pitch_type
        HAVING count(*) >= {MIN_PITCHES_PER_TYPE}
        """
    ).fetchall()

    # A stable, reproducible sample: order by a hash of the pitch key, so
    # the same database always produces the same chart.
    sample_rows = connection.execute(
        f"""
        SELECT pitcher_id, pitch_type,
               round(horizontal_break_ft * 12, 1),
               round(induced_vertical_break_ft * 12, 1)
        FROM (
            SELECT *, row_number() OVER (
                PARTITION BY pitcher_id, pitch_type
                ORDER BY hash(game_id, at_bat_number, pitch_number)
            ) AS rn
            FROM pitches
            WHERE {where} AND horizontal_break_ft IS NOT NULL
              AND induced_vertical_break_ft IS NOT NULL
        )
        WHERE rn <= {SAMPLE_PER_TYPE}
        """
    ).fetchall()

    arsenals: dict[int, list[tuple[Any, ...]]] = {}
    for row in arsenal_rows:
        arsenals.setdefault(int(row[0]), []).append(row)
    samples: dict[int, dict[str, list[list[float]]]] = {}
    for pid, code, hb, ivb in sample_rows:
        samples.setdefault(int(pid), {}).setdefault(str(code), []).append(
            [float(hb), float(ivb)]
        )

    files: list[PitcherFile] = []
    for pid, raw_name, hand, total in pitchers:
        pid = int(pid)
        arsenal: list[PitchSummary] = []
        for _, code, pname, n, velo, max_velo, spin, hb, ivb, swings, whiffs in sorted(
            arsenals.get(pid, []), key=lambda r: -int(r[3])
        ):
            arsenal.append(
                PitchSummary(
                    code=str(code),
                    name=str(pname or code),
                    count=int(n),
                    usage_pct=round(100 * int(n) / int(total), 1),
                    velocity_mph=round(float(velo), 1),
                    max_velocity_mph=round(float(max_velo), 1),
                    spin_rpm=None if spin is None else round(float(spin)),
                    horizontal_break_in=round(float(hb), 1),
                    vertical_break_in=round(float(ivb), 1),
                    whiff_pct=None
                    if not swings
                    else round(100 * int(whiffs) / int(swings), 1),
                )
            )
        codes = {p["code"] for p in arsenal}
        files.append(
            PitcherFile(
                schema_version=SCHEMA_VERSION,
                id=pid,
                name=display_name(str(raw_name)),
                hand=str(hand or "?"),
                season=season,
                pitches=int(total),
                through=through,
                arsenal=arsenal,
                movement={k: v for k, v in samples.get(pid, {}).items() if k in codes},
            )
        )
    return files, through


def validate_pitcher(pitcher: PitcherFile) -> list[str]:
    """Return every problem found; an empty list means the file is sound."""
    problems: list[str] = []
    label = f"{pitcher['name']} ({pitcher['id']})"
    if pitcher["pitches"] <= 0:
        problems.append(f"{label}: no pitches")
    if not pitcher["arsenal"]:
        problems.append(f"{label}: empty arsenal")
    if pitcher["hand"] not in ("L", "R"):
        problems.append(f"{label}: unknown hand {pitcher['hand']!r}")
    usage = sum(p["usage_pct"] for p in pitcher["arsenal"])
    if not 90.0 <= usage <= 100.5:
        problems.append(f"{label}: pitch usage adds to {usage:.1f}%")
    for p in pitcher["arsenal"]:
        lo, hi = VELOCITY_RANGE
        if not lo <= p["velocity_mph"] <= hi:
            problems.append(f"{label} {p['code']}: velocity {p['velocity_mph']}")
        if (
            p["spin_rpm"] is not None
            and not SPIN_RANGE[0] <= p["spin_rpm"] <= SPIN_RANGE[1]
        ):
            problems.append(f"{label} {p['code']}: spin {p['spin_rpm']}")
        for field, value in (
            ("horizontal_break_in", p["horizontal_break_in"]),
            ("vertical_break_in", p["vertical_break_in"]),
        ):
            if not BREAK_RANGE_IN[0] <= value <= BREAK_RANGE_IN[1]:
                problems.append(f"{label} {p['code']}: {field} {value}")
    return problems


def build_index(pitchers: list[PitcherFile], season: int, through: str) -> IndexFile:
    entries = [
        IndexEntry(
            id=p["id"],
            name=p["name"],
            hand=p["hand"],
            pitches=p["pitches"],
            arsenal=[a["code"] for a in p["arsenal"]],
        )
        for p in sorted(pitchers, key=lambda p: p["name"])
    ]
    return IndexFile(
        schema_version=SCHEMA_VERSION,
        data_version=date.today().isoformat(),
        season=season,
        through=through,
        source="Baseball Savant (MLB Statcast), regular season",
        pitchers=entries,
    )


def write(out_dir: Path, index: IndexFile, pitchers: list[PitcherFile]) -> None:
    """Replace the output folder's contents with a fresh export."""
    pitcher_dir = out_dir / "pitchers"
    if pitcher_dir.exists():
        shutil.rmtree(pitcher_dir)
    pitcher_dir.mkdir(parents=True)
    for p in pitchers:
        (pitcher_dir / f"{p['id']}.json").write_text(
            json.dumps(p, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
    (out_dir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def export(season: int, out_dir: Path, database: Path | None = None) -> IndexFile:
    with db.connect(database) as connection:
        pitchers, through = build_pitchers(connection, season)
    problems = [msg for p in pitchers for msg in validate_pitcher(p)]
    if problems:
        shown = "\n  ".join(problems[:20])
        raise ValueError(f"{len(problems)} data problems; nothing written:\n  {shown}")
    index = build_index(pitchers, season, through)
    write(out_dir, index, pitchers)
    return index


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Export pitcher JSON for the app.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    index = export(args.season, args.out)
    logger.info(
        "Exported %d pitchers through %s to %s",
        len(index["pitchers"]),
        index["through"],
        args.out,
    )


if __name__ == "__main__":
    main()
