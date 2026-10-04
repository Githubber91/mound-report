import { PitcherSearch } from "@/components/PitcherSearch";
import type { DataIndex } from "@/lib/data";
import { formatDate } from "@/lib/data";
import { pitcherHref } from "@/lib/useRoute";

/** Well-known arms to tap when you don't have a name in mind. */
const FEATURED = [
  "Paul Skenes",
  "Tarik Skubal",
  "Cristopher Sánchez",
  "Jacob Misiorowski",
];

export function HomePage({ index }: { readonly index: DataIndex }) {
  const featured = FEATURED.map((name) =>
    index.pitchers.find((p) => p.name === name),
  ).filter((p) => p !== undefined);

  return (
    <section className="pt-10 sm:pt-16">
      <p className="font-mono text-xs tracking-[0.12em] text-[var(--color-accent)] uppercase">
        {index.season} regular season · {index.pitchers.length} pitchers
      </p>
      <h1 className="mt-3 font-display text-5xl leading-[0.95] font-bold tracking-tight text-balance uppercase sm:text-6xl">
        What does he throw?
      </h1>
      <p className="mt-4 max-w-xl text-lg leading-relaxed text-pretty text-[var(--color-muted)]">
        Every MLB pitcher’s arsenal: how often he throws each pitch, how hard, how much it
        moves, and how often hitters miss it.
      </p>

      <div className="mt-8">
        <PitcherSearch pitchers={index.pitchers} autoFocus />
      </div>

      {featured.length > 0 && (
        <div className="mt-6 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-[var(--color-muted)]">Or try</span>
          {featured.map((p) => (
            <a
              key={p.id}
              href={pitcherHref(p.id)}
              className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 font-medium hover:border-[var(--color-accent)]"
            >
              {p.name}
            </a>
          ))}
        </div>
      )}

      <p className="mt-10 text-sm text-[var(--color-muted)]">
        Stats through {formatDate(index.through)}.
      </p>
    </section>
  );
}
