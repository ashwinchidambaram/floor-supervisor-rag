// BackendStatus — a quiet app-bar pill showing the live backend's reachability.
// Useful because the HF free Space sleeps + cold-starts (and runs a one-time index
// build on wake), so an interviewer can see "waking up" vs "broken". Mock/playback
// mode shows a neutral "recorded" state. Polls /health every 20s; hover = last checked.

import { useEffect, useState } from "react";
import { checkHealth, isLive } from "@/lib/dataSource";
import { cn } from "@/lib/utils";

type State = "checking" | "connected" | "waking" | "offline" | "playback";

const CFG: Record<State, { label: string; dot: string; text: string }> = {
  checking: { label: "Checking backend…", dot: "bg-ink-faint", text: "text-ink-faint" },
  connected: { label: "Backend live", dot: "bg-sage", text: "text-[#5D6A53]" },
  waking: { label: "Backend waking…", dot: "bg-gold animate-dot-pulse", text: "text-[#835C39]" },
  offline: { label: "Backend offline", dot: "bg-danger", text: "text-danger" },
  playback: { label: "Recorded demo", dot: "bg-ink-faint", text: "text-ink-faint" },
};

export function BackendStatus() {
  const live = isLive();
  const [state, setState] = useState<State>(live ? "checking" : "playback");
  const [checkedAt, setCheckedAt] = useState<Date | null>(null);

  useEffect(() => {
    if (!live) return;
    let active = true;
    const ping = async () => {
      const { reachable, indexLoaded } = await checkHealth();
      if (!active) return;
      setState(!reachable ? "offline" : indexLoaded ? "connected" : "waking");
      setCheckedAt(new Date());
    };
    ping();
    const id = setInterval(ping, 20000);
    return () => { active = false; clearInterval(id); };
  }, [live]);

  const cfg = CFG[state];
  return (
    <div
      className="flex items-center gap-1.5"
      title={checkedAt ? `last checked ${checkedAt.toLocaleTimeString()}` : "live backend status"}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} aria-hidden />
      <span className={cn("hidden font-mono text-micro lg:inline", cfg.text)}>{cfg.label}</span>
    </div>
  );
}
