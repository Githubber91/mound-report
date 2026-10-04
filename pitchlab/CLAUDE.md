# pitchlab conventions

Rules for anyone working here, human or AI. Short, with real examples.

## What this is

A Statcast pipeline and analysis workbench. Layer 1 of a portfolio project
aimed at sports analytics / AI engineering roles. Correctness and
reproducibility matter more than speed of delivery.

## Commands

| Task        | Command                      |
| ----------- | ---------------------------- |
| First setup | `./tasks.sh setup`           |
| Tests       | `./tasks.sh test`            |
| Type check  | `./tasks.sh types`           |
| Everything  | `./tasks.sh check`           |
| Get data    | `./tasks.sh season 2026`     |

Run `./tasks.sh check` before claiming work is done.

## Types

`mypy --strict` is on. Every function gets annotated parameters and a
return type.

```python
# Good
def count_pitches(connection: duckdb.DuckDBPyConnection) -> int: ...

# Avoid
def count_pitches(connection): ...
```

## Never silence the type checker to move on

`# type: ignore` needs a reason next to it. If a library genuinely has no
stubs, add it to the mypy overrides in `pyproject.toml` — that silences the
*import*, not your own code.

## Tests never touch the network

Test the pure function, not the download. Split code so this is possible:
`fetch()` talks to Statcast, `normalise()` transforms a DataFrame, and only
`normalise()` is tested.

## Fail loudly on unexpected data

Statcast changes its schema without warning. Raise rather than guess.

```python
# Good
missing = set(PITCH_COLUMNS) - set(raw.columns)
if missing:
    raise ValueError(f"Statcast response is missing columns: {sorted(missing)}")

# Avoid — silently produces a half-empty table
frame = raw.reindex(columns=list(PITCH_COLUMNS))
```

## Rename at the boundary

Statcast's column names are inconsistent and misleading (`player_name` is
the *pitcher*). Rename once, in `schema.py`, then use our names everywhere.

## Data is never committed

`data/` is rebuildable from `./tasks.sh season`. Committing it makes the repo
huge and the results unreproducible.

## Analysis rules

- Split train/test **by time**, never randomly. Random splits leak the
  future into the past and inflate every score.
- Report calibration (Brier score, log loss), not just accuracy. A model
  that says 70% must be right about 70% of the time.
- Any claim in a write-up must be reproducible from a command in the repo.
