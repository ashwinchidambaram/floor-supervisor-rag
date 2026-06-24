# PRODUCT.md

## Product Purpose

A Q/A conversational platform that is the human-facing surface of a production-style
**multi-agent system**. A user asks a question in natural language; the system (a
LangGraph multi-agent backend, currently stubbed) answers conversationally across
multiple turns. The interface is a **decoupled consumer of a data-out contract**, not a
participant in the agents. It must run and demo standalone today against a mock client,
then swap to the live backend behind the same typed interface with zero UI rework.

register: product

## Users

- **The builder / presenter** demonstrating an agentic system live, under time pressure.
  They narrate the code and the UX out loud and must be able to defend every decision.
- **A technical reviewer / interviewer** watching the demo, evaluating engineering and
  craft judgment.
- **End users** of the eventual product: people asking domain questions and reading
  multi-turn answers. The chat must feel trustworthy and legible, not like a toy.

## Brand & Tone

Client brand is **Perficient**. The product reads as a serious enterprise tool: composed,
precise, quietly confident. Not playful, not a consumer AI chat clone. The chrome carries
the brand; the conversation surface stays calm and readable so the content leads.

- **Deep teal `#154750` ("Elephant")** is the primary structural color: app rail, headers,
  key chrome. It defines hierarchy and frame.
- **Brand red `#CC2020` ("Thunderbird")** appears only as sparing accent pops (a focused
  CTA, a single live indicator), never floods, never on error.
- Status is a separate system: error/denied uses a muted `#B91C1C`, never the bright brand
  red, so "error" never reads as "brand."

## Anti-references (what this must NOT look like)

- A generic ChatGPT/Claude clone: centered bubble, lavender gradients, rounded everything,
  floating send button, no identity.
- SaaS-cream landing aesthetic, hero-metric templates, identical card grids.
- Anything where a viewer could say "an AI made that" without doubt.

## Strategic Principles

- **The conversation is the product.** Chrome frames; it never competes with the message
  thread for attention.
- **Decoupled by contract.** Every backend touch goes through one typed client. The mock
  and the real backend are interchangeable behind it.
- **Legible under narration.** The builder explains this live, so structure and naming
  must be obvious, and states (empty, loading/streaming, error) must be deliberate, not
  retrofitted.
- **Crafted, not generic.** Distinctive typographic hierarchy, intentional spatial rhythm,
  disciplined color. It should feel inevitable and specific to this product.
