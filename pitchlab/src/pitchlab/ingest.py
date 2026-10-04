"""Pull Statcast pitch data and store it locally.

Run it with:

    python -m pitchlab.ingest --season 2026
    python -m pitchlab.ingest --start 2026-07-01 --end 2026-07-07

The point of this module is *reproducibility*: anyone who clones the repo
can rebuild the database with one command. That property is what turns a
notebook into a project.

Re-running is safe. Pitches are keyed by (game, plate appearance, pitch
number), so a pitch downloaded twice replaces itself instead of doubling.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterator
from datetime import date, timedelta

import pandas as pd

from pitchlab import db
from pitchlab.config import FIRST_STATCAST_SEASON
from pitchlab.schema import PITCH_COLUMNS, PITCH_KEY

logger = logging.getLogger(__name__)

# Downloading in week-sized chunks means a dropped connection near the end
# of a season costs one week, not the whole run, and progress is visible.
CHUNK_DAYS = 7

# Spring training starts late February; the World Series ends by early
# November. A season window this wide catches every game.
SEASON_START = (2, 15)
SEASON_END = (11, 15)

REQUIRED = [
    "game_id",
    "game_date",
    "pitcher_id",
    "batter_id",
    "at_bat_number",
    "pitch_number",
]


def normalise(raw: pd.DataFrame) -> pd.DataFrame:
    """Select and rename the columns we keep, and drop unusable rows.

    Kept deliberately separate from the network call so it can be tested
    against a fixture without hitting Baseball Savant.
    """
    missing = set(PITCH_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Statcast response is missing columns: {sorted(missing)}")

    frame = raw[list(PITCH_COLUMNS)].rename(columns=PITCH_COLUMNS)

    # A pitch with no game, date, pitcher or batter is not a pitch. These
    # appear occasionally in Statcast exports and would poison later joins.
    before = len(frame)
    frame = frame.dropna(subset=REQUIRED)
    if (dropped := before - len(frame)) > 0:
        logger.warning("Dropped %d rows missing identifiers", dropped)

    frame["game_date"] = pd.to_datetime(frame["game_date"]).dt.date
    for column in ("game_id", "pitcher_id", "batter_id"):
        frame[column] = frame[column].astype("int64")
    for column in ("at_bat_number", "pitch_number"):
        frame[column] = frame[column].astype("int32")

    # Statcast occasionally repeats a row within one response.
    frame = frame.drop_duplicates(subset=list(PITCH_KEY), keep="last")

    return frame.reset_index(drop=True)


def date_chunks(
    start: date, end: date, days: int = CHUNK_DAYS
) -> Iterator[tuple[date, date]]:
    """Split [start, end] into consecutive, non-overlapping windows."""
    if end < start:
        raise ValueError("End date precedes start date")
    cursor = start
    while cursor <= end:
        stop = min(cursor + timedelta(days=days - 1), end)
        yield cursor, stop
        cursor = stop + timedelta(days=1)


def season_window(season: int, today: date | None = None) -> tuple[date, date]:
    """The date range that covers a whole season, capped at today."""
    current = today if today is not None else date.today()
    start = date(season, *SEASON_START)
    end = min(date(season, *SEASON_END), current)
    if end < start:
        raise ValueError(f"The {season} season has not started yet")
    return start, end


def fetch(start: date, end: date) -> pd.DataFrame:
    """Download raw Statcast rows for a date range."""
    if start.year < FIRST_STATCAST_SEASON:
        raise ValueError(
            f"Statcast coverage begins in {FIRST_STATCAST_SEASON}; got {start.year}"
        )
    if end < start:
        raise ValueError("End date precedes start date")

    from pybaseball import statcast  # imported late: it is slow to load

    logger.info("Fetching Statcast from %s to %s", start, end)
    raw: pd.DataFrame = statcast(
        start_dt=start.isoformat(), end_dt=end.isoformat(), verbose=False
    )
    return raw


def store(frame: pd.DataFrame) -> int:
    """Write normalised pitches, replacing any already stored. Returns the new total."""
    with db.connect() as connection:
        db.initialise(connection)
        return db.upsert_pitches(connection, frame)


def ingest_range(start: date, end: date) -> int:
    """Download and store a date range one chunk at a time. Returns pitches stored."""
    stored = 0
    for chunk_start, chunk_end in date_chunks(start, end):
        raw = fetch(chunk_start, chunk_end)
        if raw.empty:
            logger.info("No games %s to %s", chunk_start, chunk_end)
            continue
        frame = normalise(raw)
        total = store(frame)
        stored += len(frame)
        logger.info(
            "Stored %d pitches for %s to %s (database total: %d)",
            len(frame),
            chunk_start,
            chunk_end,
            total,
        )
    return stored


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Ingest Statcast pitch data.")
    parser.add_argument("--season", type=int, help="Download a whole season, e.g. 2026")
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    args = parser.parse_args()

    if args.season is not None:
        start, end = season_window(args.season)
    elif args.start is not None and args.end is not None:
        start, end = args.start, args.end
    else:
        parser.error("give either --season YEAR, or both --start and --end")

    stored = ingest_range(start, end)
    logger.info("Done: %d pitches stored for %s to %s", stored, start, end)


if __name__ == "__main__":
    main()
