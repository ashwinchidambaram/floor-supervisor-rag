// ---------------------------------------------------------------------------
// LoginGate — the access screen shown only in live mode (isLive()).
//
// Role:     A centered password field that stores its value in
//           sessionStorage["demo_access_key"], which dataSource.ask() sends as a
//           bearer. Mock mode skips this entirely; on a 401 the portal clears the
//           key and re-shows this screen.
// Contract: <LoginGate onUnlock={(key) => void} error? />.
// Failure:  empty key never submits. The portal owns 401 re-prompting.
// ---------------------------------------------------------------------------

import { useState } from "react";
import { KeyRound, Lock } from "lucide-react";

export function LoginGate({
  onUnlock,
  error,
}: {
  onUnlock: (key: string) => void;
  error?: string | null;
}) {
  const [key, setKey] = useState("");

  return (
    <div className="grid h-full place-items-center bg-canvas px-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (key.trim()) onUnlock(key.trim());
        }}
        className="w-full max-w-sm rounded-xl border border-border bg-surface px-7 py-8 shadow-card"
      >
        <span className="grid h-10 w-10 place-items-center rounded-lg bg-[rgba(212,116,94,0.10)]">
          <Lock className="h-5 w-5 text-accent" strokeWidth={2} aria-hidden />
        </span>
        <span className="eyebrow mt-5 block">◦ RESTRICTED</span>
        <h1 className="mt-2 font-display text-title font-semibold tracking-tight text-ink">
          Floor docs access
        </h1>
        <p className="mt-1.5 text-meta leading-relaxed text-ink-muted">
          Enter your access key to ask the documentation.
        </p>

        <label htmlFor="access-key" className="sr-only">
          Access key
        </label>
        <div className="mt-5 flex items-center gap-2 rounded-lg border border-border bg-surface-alt px-3 py-2.5 focus-within:border-accent/50">
          <KeyRound className="h-4 w-4 shrink-0 text-ink-faint" strokeWidth={2} aria-hidden />
          <input
            id="access-key"
            type="password"
            autoFocus
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="Access key"
            className="flex-1 bg-transparent text-body text-ink outline-none placeholder:text-ink-faint"
          />
        </div>

        {error && (
          <p className="mt-2.5 text-meta text-danger" role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={!key.trim()}
          className="mt-5 w-full rounded-lg bg-accent px-4 py-2.5 text-ui font-medium text-[#F4EFE6] shadow-glow-accent transition-colors duration-150 ease-out-quart hover:bg-accent-hover disabled:opacity-45"
        >
          Unlock
        </button>
      </form>
    </div>
  );
}
