import { useEffect, useState } from "react";
import { ArsenalTable, UsageBar } from "@/components/ArsenalTable";
import type { PitcherDetail } from "@/lib/data";
import { DataError, formatDate, loadPitcher } from "@/lib/data";

type Result =
  | { readonly status: "ready"; readonly pitcher: PitcherDetail }
  | { readonly status: "error"; readonly message: string };

type State = { readonly status: "loading" } | Result;

export function PitcherPage({ id }: { readonly id: number }) {
  // Results are remembered with the id they belong to, so moving to another
  // pitcher shows "Loading…" straight away instead of the previous pitcher.
  const [loaded, setLoaded] = useState<{
    readonly id: number;
    readonly result: Result;
  }>();
  const state: State = loaded?.id === id ? loaded.result : { status: "loading" };

  useEffect(() => {
    let current = true;
    loadPitcher(id).then(
      (pitcher) => {
        if (current) setLoaded({ id, result: { status: "ready", pitcher } });
      },
      (error: unknown) => {
        if (!current) return;
        const message =
          error instanceof DataError
            ? error.message
            : "Something went wrong loading this pitcher.";
        setLoaded({ id, result: { status: "error", message } });
      },
    );
    return () => {
      current = false;
    };
  }, [id]);

  return (
    <section className="pt-6 sm:pt-10">
      <a
        href="#/"
        className="text-sm font-medium text-[var(--color-accent)] hover:underline"
      >
        ← All pitchers
      </a>

      {state.status === "loading" && (
        <p className="mt-8 text-[var(--color-muted)]" role="status">
          Loading…
        </p>
      )}

      {state.status === "error" && (
        <p className="mt-8" role="alert">
          {state.message}
        </p>
      )}

      {state.status === "ready" && <PitcherReport pitcher={state.pitcher} />}
    </section>
  );
}

function PitcherReport({ pitcher }: { readonly pitcher: PitcherDetail }) {
  const primary = pitcher.arsenal[0];
  return (
    <article className="mt-4">
      <header>
        <p className="font-mono text-xs tracking-[0.12em] text-[var(--color-muted)] uppercase">
          {pitcher.hand === "L" ? "Left-handed pitcher" : "Right-handed pitcher"} ·{" "}
          {pitcher.season}
        </p>
        <h1 className="mt-2 font-display text-5xl leading-[0.95] font-bold tracking-tight uppercase sm:text-6xl">
          {pitcher.name}
        </h1>
        <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-3">
          <Stat label="Pitches" value={pitcher.pitches.toLocaleString("en-US")} />
          <Stat label="Pitch types" value={String(pitcher.arsenal.length)} />
          {primary && (
            <Stat
              label={`Primary · ${primary.name}`}
              value={`${primary.velocity_mph} mph`}
            />
          )}
        </dl>
      </header>

      <section aria-labelledby="mix-heading" className="mt-10">
        <h2
          id="mix-heading"
          className="mb-3 text-xs font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase"
        >
          Pitch mix
        </h2>
        <UsageBar arsenal={pitcher.arsenal} />
      </section>

      <section aria-labelledby="arsenal-heading" className="mt-10">
        <h2
          id="arsenal-heading"
          className="mb-3 text-xs font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase"
        >
          Arsenal
        </h2>
        <ArsenalTable arsenal={pitcher.arsenal} hand={pitcher.hand} />
        <p className="mt-3 text-sm leading-relaxed text-[var(--color-muted)]">
          Velocity in mph, spin in rpm, break in inches. H-Break is sideways movement
          toward his arm side or glove side; V-Break is how much the pitch rises compared
          with a spinless ball. Whiff is the share of swings that miss. Regular season
          through {formatDate(pitcher.through)}.
        </p>
      </section>
    </article>
  );
}

function Stat({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div>
      <dt className="text-xs tracking-[0.08em] text-[var(--color-muted)] uppercase">
        {label}
      </dt>
      <dd className="font-display text-3xl font-semibold tabular-nums">{value}</dd>
    </div>
  );
}
