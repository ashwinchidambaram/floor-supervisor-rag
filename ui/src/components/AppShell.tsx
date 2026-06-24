// ---------------------------------------------------------------------------
// AppShell — the shared chrome: a sticky glass TOP app-bar (matches the owner's
// personal-site TopNav) + the page slot below.
//   Role:     Orbit AC mark + wordmark + eyebrow (left), 3 surface tabs (Ask /
//             Knowledge / Observe), maker's mark (right). The page renders full-width
//             below — Ask mounts its own conversation rail inside its page.
//   Contract: { children }. Reads the active route itself for nav highlight.
//   Failure:  pure layout; pages own their empty/error states.
// ---------------------------------------------------------------------------

import type { ReactNode } from "react";
import { MessageSquareText, Library, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { navigate, useRoute, type Route } from "@/lib/router";
import { ACMonogram } from "./logo";
import { MakersMark } from "./MakersMark";

const NAV: { route: Route; label: string; icon: typeof MessageSquareText }[] = [
  { route: "/", label: "Ask", icon: MessageSquareText },
  { route: "/knowledge-base", label: "Knowledge", icon: Library },
  { route: "/observability", label: "Observe", icon: Activity },
];

export function AppShell({ children }: { children: ReactNode }) {
  const route = useRoute();
  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-canvas text-ink">
      <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-4 border-b border-border bg-surface/85 px-5 backdrop-blur-md">
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <ACMonogram size={28} variant="light" />
          <div className="leading-tight">
            <div className="font-display text-ui font-semibold tracking-tight text-ink">Floor Docs Q&amp;A</div>
            <div className="eyebrow">◦ Grounded RAG</div>
          </div>
        </div>

        {/* Surface tabs */}
        <nav className="ml-4 flex items-center gap-1" aria-label="Primary">
          {NAV.map(({ route: r, label, icon: Icon }) => {
            const active = route === r;
            return (
              <button
                key={r}
                type="button"
                onClick={() => navigate(r)}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-ui font-medium transition-colors duration-150 ease-out-quart",
                  active
                    ? "bg-[rgba(212,116,94,0.12)] text-accent"
                    : "text-ink-muted hover:bg-surface-alt hover:text-ink"
                )}
              >
                <Icon className="h-4 w-4" strokeWidth={2} />
                {label}
              </button>
            );
          })}
        </nav>

        <div className="ml-auto">
          <MakersMark />
        </div>
      </header>

      <main className="min-h-0 flex-1 overflow-hidden" data-testid="page-slot">
        {children}
      </main>
    </div>
  );
}
