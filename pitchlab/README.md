# pitchlab

A reproducible Statcast pipeline. Anyone can clone this and rebuild the
database with one command — that property is what separates a project
from a notebook.

## Setup (macOS, first time)

You need [uv](https://docs.astral.sh/uv/) (`brew install uv`). From this folder:

```bash
./tasks.sh setup     # creates .venv with Python 3.12 and installs everything
```

## Daily use

```bash
./tasks.sh season 2026              # download a whole season (30-60 min); safe to re-run
./tasks.sh ingest 2026-09-01 2026-09-07   # download a date range
./tasks.sh export 2026              # write the app's JSON to ../public/data (seconds)
./tasks.sh check                    # lint + types + tests: run before every commit
./tasks.sh test                     # just the tests
```

Downloads go one week at a time, so progress shows as it goes and a dropped
connection costs a week, not the season. Re-running any range replaces those
pitches rather than duplicating them. Each season is roughly 750,000 pitches.

## Looking at the data

```bash
uv run python -c "
from pitchlab import db
with db.connect() as c:
    print(c.execute('''
        SELECT pitch_type, count(*) AS n, round(avg(velocity_mph), 1) AS mph
        FROM pitches GROUP BY 1 ORDER BY n DESC
    ''').fetchdf())
"
```

## Layout

| Path                      | What it holds                                   |
| ------------------------- | ----------------------------------------------- |
| `src/pitchlab/schema.py`  | Which columns we keep and what we call them     |
| `src/pitchlab/ingest.py`  | Download → clean → store                        |
| `src/pitchlab/db.py`      | DuckDB access                                   |
| `src/pitchlab/export.py`  | Database → validated JSON for the app           |
| `tests/`                  | Tests that run offline against a fixture        |
| `data/`                   | The database. Rebuildable with `./tasks.sh season`; never committed.     |

## Why these choices

**DuckDB** — a single file that speaks fast analytical SQL. No server, no
Docker, no credentials. The SQL skills transfer directly to the job.

**mypy strict** — the same bargain as the strict `tsconfig.json`: say what
your data is, and the computer catches the mistakes.

**Tests against a fixture, not the network** — tests that need the internet
fail for reasons unrelated to your code, so you stop trusting them.
