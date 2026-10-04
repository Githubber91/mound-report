/**
 * Loading the pitch data the Python pipeline exports to `public/data/`.
 *
 * The shapes here mirror `pitchlab/src/pitchlab/export.py`. When that file
 * bumps SCHEMA_VERSION, bump it here too: the check below makes an app
 * that doesn't understand new data say so instead of showing nonsense.
 */

export const SCHEMA_VERSION = 1;

export type Hand = "L" | "R";

export interface PitcherSummary {
  readonly id: number;
  readonly name: string;
  readonly hand: Hand;
  readonly pitches: number;
  readonly arsenal: readonly string[];
}

export interface DataIndex {
  readonly schema_version: number;
  readonly data_version: string;
  readonly season: number;
  readonly through: string;
  readonly source: string;
  readonly pitchers: readonly PitcherSummary[];
}

export interface Pitch {
  readonly code: string;
  readonly name: string;
  readonly count: number;
  readonly usage_pct: number;
  readonly velocity_mph: number;
  readonly max_velocity_mph: number;
  readonly spin_rpm: number | null;
  /** Catcher's view, inches: positive is toward first base. */
  readonly horizontal_break_in: number;
  /** Induced vertical break, inches: positive is "rise" against gravity. */
  readonly vertical_break_in: number;
  readonly whiff_pct: number | null;
}

export interface PitcherDetail {
  readonly schema_version: number;
  readonly id: number;
  readonly name: string;
  readonly hand: Hand;
  readonly season: number;
  readonly pitches: number;
  readonly through: string;
  readonly arsenal: readonly Pitch[];
  /** Sampled [horizontal, vertical] break points in inches, per pitch code. */
  readonly movement: Readonly<Record<string, readonly (readonly [number, number])[]>>;
}

export class DataError extends Error {
  override name = "DataError";
}

function dataUrl(path: string): string {
  return `${import.meta.env.BASE_URL}data/${path}`;
}

async function getJson(path: string): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(dataUrl(path));
  } catch {
    throw new DataError("Couldn't load the stats. Check your connection and try again.");
  }
  if (response.status === 404)
    throw new DataError("We don't have stats for that pitcher.");
  if (!response.ok)
    throw new DataError(`The stats didn't load (error ${response.status}).`);
  return response.json();
}

function checkSchema(value: unknown): void {
  if (typeof value !== "object" || value === null || !("schema_version" in value)) {
    throw new DataError("The stats file is damaged.");
  }
  if (value.schema_version !== SCHEMA_VERSION) {
    throw new DataError("This version of the app is out of date. Please update it.");
  }
}

export async function loadIndex(): Promise<DataIndex> {
  const value = await getJson("index.json");
  checkSchema(value);
  return value as DataIndex;
}

export async function loadPitcher(id: number): Promise<PitcherDetail> {
  const value = await getJson(`pitchers/${id}.json`);
  checkSchema(value);
  return value as PitcherDetail;
}

/** Lowercase and strip accents, so "sanchez" finds "Sánchez". */
export function normalise(text: string): string {
  return text
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

/**
 * Pitchers whose name matches every word typed, best matches first:
 * names starting with the query, then surnames starting with it, then the
 * rest, each group ordered by pitches thrown (regulars before call-ups).
 */
export function searchPitchers(
  pitchers: readonly PitcherSummary[],
  query: string,
  limit = 12,
): PitcherSummary[] {
  const q = normalise(query);
  if (!q) return [];
  const words = q.split(/\s+/);

  const scored: { pitcher: PitcherSummary; rank: number }[] = [];
  for (const pitcher of pitchers) {
    const name = normalise(pitcher.name);
    if (!words.every((word) => name.includes(word))) continue;
    const surname = name.split(" ").slice(1).join(" ");
    const rank = name.startsWith(q) ? 0 : surname.startsWith(q) ? 1 : 2;
    scored.push({ pitcher, rank });
  }
  scored.sort((a, b) => a.rank - b.rank || b.pitcher.pitches - a.pitcher.pitches);
  return scored.slice(0, limit).map((s) => s.pitcher);
}

/**
 * Horizontal break from the pitcher's side: positive means "arm side"
 * (toward the throwing arm), negative "glove side". This is how coaches
 * talk, and it lets lefties and righties be compared directly.
 */
export function armSideBreak(horizontalBreakIn: number, hand: Hand): number {
  return hand === "R" ? -horizontalBreakIn : horizontalBreakIn;
}

export function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return iso;
  return new Date(y, m - 1, d).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}
