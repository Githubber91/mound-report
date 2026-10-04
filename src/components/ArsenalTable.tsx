import type { Hand, Pitch } from "@/lib/data";
import { armSideBreak } from "@/lib/data";
import { pitchColor } from "@/lib/pitchTypes";

interface ArsenalProps {
  readonly arsenal: readonly Pitch[];
  readonly hand: Hand;
}

/** One stacked bar showing the whole pitch mix at a glance. */
export function UsageBar({ arsenal }: { readonly arsenal: readonly Pitch[] }) {
  return (
    <div>
      <div
        className="flex h-4 w-full overflow-hidden rounded-full bg-[var(--color-border)]"
        role="img"
        aria-label={`Pitch mix: ${arsenal.map((p) => `${p.name} ${p.usage_pct}%`).join(", ")}`}
      >
        {arsenal.map((pitch) => (
          <span
            key={pitch.code}
            style={{
              width: `${pitch.usage_pct.toFixed(1)}%`,
              backgroundColor: pitchColor(pitch.code),
            }}
            className="h-full border-r-2 border-[var(--color-surface)] last:border-r-0"
          />
        ))}
      </div>
      <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-sm">
        {arsenal.map((pitch) => (
          <li key={pitch.code} className="flex items-center gap-1.5">
            <span
              aria-hidden="true"
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: pitchColor(pitch.code) }}
            />
            {pitch.name}{" "}
            <span className="font-mono text-[var(--color-muted)] tabular-nums">
              {pitch.usage_pct.toFixed(1)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function fmt(value: number | null, digits = 1): string {
  return value === null ? "–" : value.toFixed(digits);
}

function sideLabel(armSide: number): string {
  if (Math.abs(armSide) < 0.5) return "";
  return armSide > 0 ? "arm" : "glove";
}

export function ArsenalTable({ arsenal, hand }: ArsenalProps) {
  return (
    <div className="overflow-x-auto rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)]">
      <table className="w-full min-w-[640px] border-collapse text-left text-[0.95rem]">
        <caption className="sr-only">
          Pitch-by-pitch averages. Break is in inches; horizontal break is measured toward
          the pitcher’s arm side or glove side.
        </caption>
        <thead>
          <tr className="border-b border-[var(--color-border)] text-xs tracking-[0.08em] text-[var(--color-muted)] uppercase">
            <th
              scope="col"
              className="sticky left-0 bg-[var(--color-surface)] px-4 py-3 font-semibold"
            >
              Pitch
            </th>
            <th scope="col" className="px-3 py-3 text-right font-semibold">
              Usage
            </th>
            <th scope="col" className="px-3 py-3 text-right font-semibold">
              Velo
            </th>
            <th scope="col" className="px-3 py-3 text-right font-semibold">
              Top
            </th>
            <th scope="col" className="px-3 py-3 text-right font-semibold">
              Spin
            </th>
            <th scope="col" className="px-3 py-3 text-right font-semibold">
              H-Break
            </th>
            <th scope="col" className="px-3 py-3 text-right font-semibold">
              V-Break
            </th>
            <th scope="col" className="px-4 py-3 text-right font-semibold">
              Whiff
            </th>
          </tr>
        </thead>
        <tbody className="font-mono text-sm tabular-nums">
          {arsenal.map((pitch) => {
            const armSide = armSideBreak(pitch.horizontal_break_in, hand);
            return (
              <tr
                key={pitch.code}
                className="border-b border-[var(--color-border)] last:border-b-0"
              >
                <th
                  scope="row"
                  className="sticky left-0 bg-[var(--color-surface)] px-4 py-3 font-sans text-[0.95rem] font-semibold"
                >
                  <span className="flex items-center gap-2">
                    <span
                      aria-hidden="true"
                      className="h-3 w-3 shrink-0 rounded-full"
                      style={{ backgroundColor: pitchColor(pitch.code) }}
                    />
                    {pitch.name}
                  </span>
                </th>
                <td className="px-3 py-3 text-right">{fmt(pitch.usage_pct)}%</td>
                <td className="px-3 py-3 text-right">{fmt(pitch.velocity_mph)}</td>
                <td className="px-3 py-3 text-right text-[var(--color-muted)]">
                  {fmt(pitch.max_velocity_mph)}
                </td>
                <td className="px-3 py-3 text-right">{fmt(pitch.spin_rpm, 0)}</td>
                <td className="px-3 py-3 text-right">
                  {fmt(Math.abs(armSide))}
                  <span className="ml-1 font-sans text-xs text-[var(--color-muted)]">
                    {sideLabel(armSide)}
                  </span>
                </td>
                <td className="px-3 py-3 text-right">{fmt(pitch.vertical_break_in)}</td>
                <td className="px-4 py-3 text-right">
                  {pitch.whiff_pct === null ? "–" : `${fmt(pitch.whiff_pct)}%`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
