# Project conventions

Rules for anyone working in this repo — human or AI assistant. Keep this file
short and full of real examples. Vague rules get ignored by both audiences.

## Stack

Vite + React 19 + TypeScript. Tailwind v4. Vitest. pnpm. ESM only.

## Commands

| Task       | Command          |
| ---------- | ---------------- |
| Dev server | `pnpm dev`       |
| Type check | `pnpm typecheck` |
| Tests      | `pnpm test`      |
| Everything | `pnpm check`     |

Run `pnpm check` before claiming work is done. It is the same gate CI runs.

## Return types

Declare return types on module-level functions. This states intent rather than
leaving it to be inferred, which helps both future readers and models.

```ts
// Good
export function totalMinutes(items: readonly Lesson[]): number {
  return items.reduce((sum, lesson) => sum + lesson.minutes, 0);
}

// Avoid — the contract is implicit
export function totalMinutes(items: readonly Lesson[]) {
  return items.reduce((sum, lesson) => sum + lesson.minutes, 0);
}
```

Exception: React components returning JSX. Let those infer.

## Type imports

`verbatimModuleSyntax` is on, so a type-only import must say so.

```ts
import type { Lesson } from "@/lib/lessons"; // types only
import { lessons } from "@/lib/lessons"; // real runtime value
```

## Never use `any`

If a type is genuinely unknown, use `unknown` and narrow it. `any` disables the
compiler exactly where you most need it.

```ts
// Good
function parse(input: unknown): Lesson {
  if (typeof input !== "object" || input === null) throw new Error("not an object");
  // ...narrow further
}
```

## Array access returns `T | undefined`

`noUncheckedIndexedAccess` is on. This is deliberate. Handle the missing case;
do not reach for `!` to silence it.

```ts
// Good
const first = lessons[0];
if (!first) return null;

// Avoid
const first = lessons[0]!;
```

## Imports

Use the `@/` alias for anything inside `src`. No `../../..` chains.

```ts
import { LessonCard } from "@/components/LessonCard"; // good
import { LessonCard } from "../../components/LessonCard"; // avoid
```

## Styling

- All colour, type and radius values live as tokens in `src/index.css` under
  `@theme`. Components reference `var(--color-ink)` and friends — they never
  hardcode a hex value.
- Every colour must work in both light and dark mode. Check both.
- Interactive elements need a visible `:focus-visible` state and an accessible
  name. An icon-only button needs `aria-label`.
- Respect `prefers-reduced-motion` for anything that animates.

## Tests

Colocate as `*.test.ts(x)` next to the code. Test behaviour through the public
surface, not internals. Query by role and accessible name rather than test IDs —
if a query is hard to write, the markup is probably inaccessible.

## Comments

Explain _why_, not _what_. If a line needs a comment to explain what it does,
rename things until it does not.
