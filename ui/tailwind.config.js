/**
 * Tailwind config — "Warm Frontier" design tokens for the Floor Docs Q&A UI.
 *
 * Role: single source of truth for color / type / radius / motion. Colors are CSS
 * variables defined in index.css (Cosmic-light hex); this file maps semantic Tailwind
 * names onto them so components reference roles (bg-canvas, text-ink, bg-accent).
 *
 * Brand discipline (locked):
 *   - accent (terracotta #D4745E) = interactive / selection / brand ONLY, never a status.
 *   - sage #8B9D83 = good/HIGH · gold #D4A574 = caution/MEDIUM · danger #D85650 = LOW/abstain/error.
 */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        surface: "var(--surface)",
        "surface-alt": "var(--surface-alt)",
        "surface-sunken": "var(--surface-alt)",
        border: "var(--border)",
        "border-subtle": "var(--border-subtle)",
        "border-strong": "var(--border-subtle)",
        // short alias so `border-subtle` / `divide-subtle` resolve (the lighter divider)
        subtle: "var(--border-subtle)",

        ink: "var(--ink)",
        "ink-muted": "var(--ink-muted)",
        "ink-faint": "var(--ink-faint)",

        // accent — terracotta, interactive/brand only (NEVER status).
        // RGB-channel form so BOTH solid (bg-accent) AND opacity modifiers (bg-accent/45,
        // ring-accent/70, focus-within:border-accent/50) resolve. A hex var can't do the latter.
        accent: {
          DEFAULT: "rgb(var(--accent-rgb) / <alpha-value>)",
          hover: "rgb(var(--accent-hover-rgb) / <alpha-value>)",
        },

        // semantic status — disjoint from accent
        sage: "var(--sage)",
        gold: "var(--gold)",
        danger: "var(--danger)",
        "danger-soft": "var(--danger-soft)",
        // aliases so existing classes keep resolving during migration
        success: "var(--sage)",
        amber: "var(--gold)",

        ring: "var(--ring)",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        display: ["Space Grotesk", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      fontSize: {
        micro: ["0.6875rem", { lineHeight: "1rem", letterSpacing: "0.04em" }],
        meta: ["0.8125rem", { lineHeight: "1.2rem" }],
        ui: ["0.875rem", { lineHeight: "1.3rem" }],
        body: ["1rem", { lineHeight: "1.6rem" }],
        lead: ["1.125rem", { lineHeight: "1.75rem" }],
        title: ["1.375rem", { lineHeight: "1.75rem", letterSpacing: "-0.012em" }],
        display: ["1.75rem", { lineHeight: "2.05rem", letterSpacing: "-0.02em" }],
      },
      maxWidth: { reading: "46rem", wide: "72rem" },
      borderRadius: { sm: "0.375rem", DEFAULT: "0.5rem", lg: "0.75rem", xl: "1rem" },
      boxShadow: {
        card: "0 2px 10px rgba(11,30,54,0.05)",
        pop: "0 16px 44px rgba(11,30,54,0.16)",
        "glow-accent": "0 0 12px rgba(212,116,94,0.25)",
        composer: "0 1px 2px rgba(11,30,54,0.04), 0 8px 24px -12px rgba(11,30,54,0.16)",
      },
      transitionTimingFunction: {
        "out-quart": "cubic-bezier(0.165, 0.84, 0.44, 1)",
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "dot-pulse": {
          "0%, 100%": { opacity: "0.35", transform: "scale(0.85)" },
          "50%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.32s cubic-bezier(0.16, 1, 0.3, 1) both",
        "dot-pulse": "dot-pulse 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
