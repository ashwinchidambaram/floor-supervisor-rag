# Agentic Q&A — Demo UI

A multi-turn **Q/A conversational interface** for the multi-agent system, with a
**conversation-history** sidebar. It is a fully decoupled **consumer of a typed client
contract**: it runs and demos standalone today against a mock backend, and swaps to the real
multi-agent backend later behind the *same* interface, with zero UI changes.

Built with React + Vite + TypeScript + Tailwind + shadcn-style primitives (Radix). Design
follows the Perficient brand: deep teal `#154750` structural chrome, brand red `#CC2020` as a
sparing accent (never error), error red `#B91C1C` kept separate.

---

## What it does

- **Multi-turn chat**: ask a question, get a streaming-style assistant reply; full message
  history within a conversation. Designed empty / thinking / streaming / error states.
- **Conversation history** (left rail): new, switch, rename, delete. Conversations and the
  last-open selection **persist across page reloads** (localStorage today).
- **Accessibility**: keyboard send (Enter / Shift+Enter), visible teal focus rings, `role="log"`
  + `aria-live` on the message thread, ≥44px touch targets, reduced-motion honored.

---

## Run it

```bash
cd ui
npm install
npm run dev      # http://localhost:5173
```

```bash
npm run build    # type-check (tsc -b) + production build — must be green
npm run preview  # serve the production build
```

## Run the Playwright tests (headless)

```bash
cd ui
npm install
npx playwright install chromium   # once, to fetch the browser
npm run test:e2e                  # boots the dev server + runs headless Chromium
```

The suite (`tests/chat.spec.ts`) verifies, against the mock: the chat surface renders with **no
console errors** and the empty state shows; a **multi-turn** exchange (two user turns + two
assistant replies, in order); **persistence across reload**; **switching** loads the correct
history; **rename**; **delete**; and the **error state** (inline error + retry) via an armed
fault. All 7 pass headless.

> Demoing the error state by hand: open `http://localhost:5173/?fail=1` and send a message, or
> set `window.__chatFail = true` in the console. The user's message is preserved; the assistant
> turn errors with a retry.

---

## Mocked vs. real (the demo boundary)

| Concern | Today (mock) | Later (real) |
|---|---|---|
| Conversations CRUD | `localStorage` | backend store via `fetch` |
| Assistant replies | canned, varied, simulated streaming | the multi-agent system, streamed over SSE/`ReadableStream` |
| Persistence | browser `localStorage` | server-side (checkpointer / DB) |

Everything the UI knows about the backend lives in **`src/lib/types.ts`** (the `ChatClient`
interface + domain types). Nothing in the UI reaches past it into agent internals.

---

## The wiring seam (how we plug in the real backend)

There is exactly **one** place to swap implementations:

**File:** `src/lib/chatClient.ts`
**Change:** the single export line.

```ts
// today
export const chatClient: ChatClient = mockChatClient;

// later
export const chatClient: ChatClient = httpChatClient;
```

To go live:

1. Implement **`src/lib/httpChatClient.ts`** against the `ChatClient` interface in
   `src/lib/types.ts` — `fetch` for the CRUD methods, and an SSE / `ReadableStream` reader for
   `sendMessage` (it must return an `AsyncIterable<string>` of token chunks, same as the mock).
2. Flip the one export line in `src/lib/chatClient.ts`.

No components change, no types change, no test changes. The mock
(`src/lib/mockChatClient.ts`) documents the exact contract each method must honor (including
"persist the user turn before streaming, so it survives a mid-stream failure").

---

## Structure

```
ui/
├── index.html
├── tailwind.config.js        # design tokens (color/type/motion) — single source of truth
├── playwright.config.ts
├── PRODUCT.md / DESIGN.md     # impeccable design context (users, brand, tokens, rationale)
├── src/
│   ├── main.tsx · App.tsx     # shell: wires the orchestrator hook to presentational components
│   ├── index.css              # OKLCH tokens, focus styles, reduced-motion
│   ├── lib/
│   │   ├── types.ts           # ChatClient interface + domain types  ← the contract
│   │   ├── chatClient.ts      # THE SEAM: which implementation is live
│   │   ├── mockChatClient.ts  # localStorage + simulated streaming (swap target)
│   │   ├── useConversations.ts# the only stateful caller of the client
│   │   ├── format.ts · utils.ts
│   └── components/
│       ├── ConversationRail.tsx      # teal history sidebar + maker's mark
│       ├── ConversationDialogs.tsx   # rename / confirm-delete
│       ├── ConversationHeader.tsx    # live status bar
│       ├── MessageThread.tsx         # the conversation log (streaming, error+retry)
│       ├── Composer.tsx              # input + send
│       ├── EmptyState.tsx            # first-run + empty-thread starters
│       └── ui/                       # shadcn-style primitives (button, dialog, menu, tooltip)
└── tests/chat.spec.ts         # headless Playwright self-validation
```

## Maker's mark

A small placeholder monogram (`AC`) + one line of mono text sits in the **rail footer**,
deliberately separate from the Perficient brand (muted, no brand color). Swap the placeholder
for a real logo where marked in `src/components/ConversationRail.tsx` (`<img src="/your-logo.svg" />`).
