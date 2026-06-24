// MakersMark — quiet non-brand attribution at the app-bar's far edge.
// >>> SWAP A REAL LOGO HERE <<< replace the "ac" span with <img src="/your-mark.svg" .../>.
// Keep it muted/mono, never brand-colored, never in a brand position.
export function MakersMark() {
  return (
    <div className="flex items-center gap-2 text-ink-faint">
      <span
        aria-hidden
        className="grid h-5 w-5 place-items-center rounded border border-border font-mono text-[0.6rem] font-semibold"
      >
        ac
      </span>
      <span className="hidden font-mono text-micro sm:inline">crafted by a. chidambaram</span>
    </div>
  );
}
