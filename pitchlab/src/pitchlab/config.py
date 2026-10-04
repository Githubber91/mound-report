"""Paths and settings. One place, so nothing hardcodes a location."""

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DATABASE_PATH: Final[Path] = DATA_DIR / "pitchlab.duckdb"

# Statcast has full pitch-tracking coverage from 2015 onward. Earlier
# seasons exist but the columns are inconsistent, so we refuse them
# rather than silently ingesting junk.
FIRST_STATCAST_SEASON: Final[int] = 2015
