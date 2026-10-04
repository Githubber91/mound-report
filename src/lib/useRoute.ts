import { useEffect, useState } from "react";

/**
 * Hash-based routes (`#/pitcher/694973`). They work on any static host and
 * inside the Android app with no server configuration, and every pitcher
 * page gets a shareable link.
 */
export type Route =
  | { readonly page: "home" }
  | { readonly page: "pitcher"; readonly id: number }
  | { readonly page: "about" };

export function parseRoute(hash: string): Route {
  const path = hash.replace(/^#\/?/, "");
  const pitcher = /^pitcher\/(\d+)$/.exec(path);
  if (pitcher?.[1]) return { page: "pitcher", id: Number(pitcher[1]) };
  if (path === "about") return { page: "about" };
  return { page: "home" };
}

export function pitcherHref(id: number): string {
  return `#/pitcher/${id}`;
}

export function useRoute(): Route {
  const [route, setRoute] = useState<Route>(() => parseRoute(window.location.hash));
  useEffect(() => {
    const onChange = (): void => {
      setRoute(parseRoute(window.location.hash));
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
