# DESIGN.md

## Theme — the physical scene

A reviewer and a builder sit side by side in a bright conference room, mid-morning, daylight
on the screen, evaluating a serious enterprise tool. The mood is composed and attentive, not
nocturnal. That forces **light**: a near-white, teal-tinted page that reads as clean
enterprise software in daylight, with the deep-teal rail anchoring the frame. Dark mode is
not built; this is a single, committed light surface.

## Color strategy — Restrained-plus-structural

Tinted neutrals carry the surface. **Deep teal** is the structural frame (the rail), used as
a committed block of identity, not an accent. **Brand red** is a true accent, kept under ~5%
of any view: a single live/send affordance and a focus pop. Status colors are a separate
semantic system from brand.

All colors authored in **OKLCH**; neutrals are tinted toward the teal hue (chroma ~0.006) so
nothing is a dead gray. No pure `#000`/`#fff`.

| Role | Hex (brief-locked) | OKLCH (authored) | Use |
|---|---|---|---|
| Teal / structural | `#154750` | `oklch(0.34 0.05 199)` | App rail, headers, active states, assistant mark |
| Teal hover/deep | — | `oklch(0.29 0.05 199)` | Rail hover, pressed |
| Brand red / accent | `#CC2020` | `oklch(0.55 0.20 27)` | Send when ready, live dot — sparing pops only |
| Page bg | `#F7F8F9` | `oklch(0.98 0.002 220)` | Main canvas |
| Surface (raised) | `#FFFFFF` | `oklch(1 0 0)` tinted → `oklch(0.995 0.002 220)` | Composer, message surfaces |
| Border | `#E5E7EB` | `oklch(0.91 0.004 220)` | Hairlines, dividers |
| Body text | `#1F2937` | `oklch(0.30 0.02 250)` | Default text |
| Muted text | — | `oklch(0.52 0.015 230)` | Timestamps, secondary labels |
| Error (denied) | `#B91C1C` | `oklch(0.50 0.18 27)` | Error states only — NEVER brand red |
| Success | — | `oklch(0.55 0.11 155)` | Approved/ok status |
| Amber | — | `oklch(0.74 0.13 75)` | Pending/in-review status |

## Typography

- **Display / UI sans:** a humanist grotesque. Use a system-safe stack with a crafted
  feel: `"Inter"` first, then system fallbacks. Headings get tighter tracking and weight,
  not just larger size.
- **Conversation body:** same family, but message text sits at a comfortable reading
  measure (max ~68ch) and a slightly larger line-height for calm legibility.
- **Mono accent:** `ui-monospace` for the maker's mark and any code spans.
- Hierarchy via scale + weight, ratio ≥1.25 between steps. Conversation title is the
  loudest in-content element; assistant/user role labels are quiet uppercase micro-labels
  with tracking, not big.

Type scale (rem): 0.6875 (micro), 0.8125 (meta), 0.875 (ui), 0.9375 (body), 1.0625 (lead),
1.375 (title), 1.75 (display).

## Layout & rhythm

- Two columns: a fixed **left rail** (conversation history, ~17rem) on deep teal, and the
  **conversation column** on the page bg. The composer is docked at the bottom of the
  conversation column, the thread scrolls above it.
- Conversation content is centered in a reading column (max ~46rem) so long answers stay at
  65–75ch, with generous breathing room. Messages are NOT chat bubbles in a card grid; user
  and assistant turns are differentiated by alignment, a quiet role micro-label, and a
  surface/weight shift, with full-width hairline rhythm between exchanges.
- Spacing varies for rhythm: tight within a turn, open between exchanges.
- No nested cards. The composer is a single raised surface; messages live on the canvas.

## Elevation

Flat-forward. One elevation level for the composer and the rail edge (a hairline + a very
soft, low shadow). No decorative shadows, no glassmorphism.

## Motion

- Streaming reply: tokens append; a soft caret/typing indicator while in flight. Ease-out
  (expo/quart), 150–260ms for UI transitions. No bounce, no elastic.
- New message scroll-into-view is smooth, respects `prefers-reduced-motion`.
- Rail item hover/active is a quick background/teal shift, not a transform.

## Components (primitives)

shadcn/ui as the base, restyled to these tokens: Button, Input/Textarea, ScrollArea,
DropdownMenu (rename/delete), Dialog (rename, confirm delete), Tooltip. Everything else is
composed in-repo. Focus states are designed (teal ring, visible), not browser-default.

## Accessibility

WCAG AA contrast on all text. Keyboard: send on Enter (Shift+Enter newline), full keyboard
nav of the rail, focus-visible rings. Touch targets ≥44px. Semantic roles for the message
log (`role="log"`, `aria-live="polite"` on the streaming region). Reduced-motion honored.

## Maker's mark

A small monogram + one line of mono text in the **rail footer**, visually separate from the
Perficient brand (muted, no brand color, smaller). Placeholder mark with a comment showing
where to swap a real `<img>` logo.
