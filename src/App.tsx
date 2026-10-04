import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";
import type { DataIndex } from "@/lib/data";
import { DataError, loadIndex } from "@/lib/data";
import { useRoute } from "@/lib/useRoute";
import { HomePage } from "@/pages/HomePage";
import { PitcherPage } from "@/pages/PitcherPage";

type IndexState =
  | { readonly status: "loading" }
  | { readonly status: "ready"; readonly index: DataIndex }
  | { readonly status: "error"; readonly message: string };

export function App() {
  const route = useRoute();
  const [index, setIndex] = useState<IndexState>({ status: "loading" });

  useEffect(() => {
    loadIndex().then(
      (value) => setIndex({ status: "ready", index: value }),
      (error: unknown) =>
        setIndex({
          status: "error",
          message: error instanceof DataError ? error.message : "Something went wrong.",
        }),
    );
  }, []);

  return (
    <div className="min-h-dvh">
      <div className="mx-auto w-full max-w-3xl px-4 py-5 sm:px-6">
        <header className="flex items-center justify-between">
          <a
            href="#/"
            className="font-display text-xl font-bold tracking-[0.04em] uppercase"
            aria-label="Mound Report home"
          >
            Mound <span className="text-[var(--color-accent)]">Report</span>
          </a>
          <ThemeToggle />
        </header>

        <main>
          {route.page === "pitcher" ? (
            <PitcherPage id={route.id} />
          ) : index.status === "ready" ? (
            <HomePage index={index.index} />
          ) : index.status === "error" ? (
            <p className="pt-16" role="alert">
              {index.message}
            </p>
          ) : (
            <p className="pt-16 text-[var(--color-muted)]" role="status">
              Loading pitchers…
            </p>
          )}
        </main>

        <footer className="mt-20 border-t border-[var(--color-border)] pt-6 pb-8 text-sm leading-relaxed text-[var(--color-muted)]">
          <p>
            Data from Baseball Savant (MLB Statcast). Mound Report is an independent
            project and is not affiliated with or endorsed by Major League Baseball.
          </p>
        </footer>
      </div>
    </div>
  );
}
