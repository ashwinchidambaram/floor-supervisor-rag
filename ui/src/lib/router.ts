// ---------------------------------------------------------------------------
// router.ts — dependency-free hash router for the 3-surface shell.
//   Role:     map the URL hash to a Route + expose hash query params (?c=, ?thread=)
//             without react-router. Static `dist/` works from any path, no rewrites.
//   Contract: useRoute() -> Route; navigate(route) sets the hash (preserving the surface);
//             useHashParam(key) -> [value|null, setter] for ?c=/?thread= deep-links.
//   Failure:  unknown hash → "/" (Ask).
// ---------------------------------------------------------------------------

import { useEffect, useState } from "react";

export type Route = "/" | "/observability" | "/knowledge-base";
const ROUTES: Route[] = ["/", "/observability", "/knowledge-base"];

function parse(): { route: Route; query: URLSearchParams } {
  const raw = window.location.hash.replace(/^#/, "") || "/";
  const [path, qs = ""] = raw.split("?");
  const route = (ROUTES.includes(path as Route) ? path : "/") as Route;
  return { route, query: new URLSearchParams(qs) };
}

function writeHash(route: Route, query: URLSearchParams): void {
  const qs = query.toString();
  const next = qs ? `${route}?${qs}` : route;
  if (window.location.hash.replace(/^#/, "") !== next) window.location.hash = next;
}

export function readRoute(): Route {
  return parse().route;
}

/** Navigate to a surface (resets that surface's query params). */
export function navigate(route: Route): void {
  writeHash(route, new URLSearchParams());
}

/** Subscribe to the current route; re-renders on hashchange. */
export function useRoute(): Route {
  const [route, setRoute] = useState<Route>(readRoute);
  useEffect(() => {
    const on = () => setRoute(readRoute());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}

/** Read/write a single hash query param (e.g. ?c=<convId> on Ask, ?thread=<turnId> on Observe). */
export function useHashParam(key: string): [string | null, (v: string | null) => void] {
  const [val, setVal] = useState<string | null>(() => parse().query.get(key));
  useEffect(() => {
    const on = () => setVal(parse().query.get(key));
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, [key]);
  const set = (v: string | null) => {
    const { route, query } = parse();
    if (v === null) query.delete(key);
    else query.set(key, v);
    writeHash(route, query);
  };
  return [val, set];
}
