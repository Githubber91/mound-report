import { useId, useMemo, useState } from "react";
import type { PitcherSummary } from "@/lib/data";
import { searchPitchers } from "@/lib/data";
import { pitchColor } from "@/lib/pitchTypes";
import { pitcherHref } from "@/lib/useRoute";

interface PitcherSearchProps {
  readonly pitchers: readonly PitcherSummary[];
  readonly autoFocus?: boolean;
}

export function PitcherSearch({ pitchers, autoFocus = false }: PitcherSearchProps) {
  const [query, setQuery] = useState("");
  const inputId = useId();
  const resultsId = useId();
  const results = useMemo(() => searchPitchers(pitchers, query), [pitchers, query]);
  const showEmpty = query.trim().length > 0 && results.length === 0;

  return (
    <form
      role="search"
      onSubmit={(event) => {
        event.preventDefault();
        const first = results[0];
        if (first) window.location.hash = pitcherHref(first.id);
      }}
    >
      <label
        htmlFor={inputId}
        className="text-xs font-semibold tracking-[0.12em] text-[var(--color-muted)] uppercase"
      >
        Find a pitcher
      </label>
      <input
        id={inputId}
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Try Skenes, Skubal or Sánchez"
        autoComplete="off"
        autoCorrect="off"
        spellCheck={false}
        // Focusing the box on the home page is the whole point of the page.
        autoFocus={autoFocus}
        aria-controls={resultsId}
        className="mt-2 w-full rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3.5 text-lg text-[var(--color-ink)] placeholder:text-[var(--color-muted)] focus:border-[var(--color-accent)] focus:outline-none focus-visible:outline-2"
      />

      <div id={resultsId} aria-live="polite">
        {results.length > 0 && (
          <ul
            aria-label="Matching pitchers"
            className="mt-2 divide-y divide-[var(--color-border)] overflow-hidden rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)]"
          >
            {results.map((pitcher) => (
              <li key={pitcher.id}>
                <a
                  href={pitcherHref(pitcher.id)}
                  className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-[var(--color-accent-soft)] focus-visible:bg-[var(--color-accent-soft)]"
                >
                  <span className="min-w-0">
                    <span className="block truncate font-semibold">{pitcher.name}</span>
                    <span className="text-sm text-[var(--color-muted)]">
                      {pitcher.hand === "L" ? "LHP" : "RHP"} ·{" "}
                      {pitcher.pitches.toLocaleString("en-US")} pitches
                    </span>
                  </span>
                  <span className="flex shrink-0 gap-1" aria-hidden="true">
                    {pitcher.arsenal.slice(0, 6).map((code) => (
                      <span
                        key={code}
                        title={code}
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: pitchColor(code) }}
                      />
                    ))}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        )}
        {showEmpty && (
          <p className="mt-3 text-sm text-[var(--color-muted)]">
            No pitcher matches “{query.trim()}”. Pitchers need at least 100 regular-season
            pitches to appear.
          </p>
        )}
      </div>
    </form>
  );
}
