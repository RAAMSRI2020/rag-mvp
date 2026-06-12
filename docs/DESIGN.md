# rag-mvp — Design & Problem Analysis (v2 thinking)

This document is the "why," not the "what." It frames the project as a problem
space so every code decision has a reason behind it. Read top to bottom; the
last two sections (memory layer and evaluation) are where the real value is.

---

## 1. The actual problem

"Answer questions from chat-history PDFs like a human" is not one problem. It is
a chain of distinct problems, each currently attacked with a local hack:

1. Recover conversation structure from a PDF.
2. Slice it into retrievable units.
3. Retrieve the relevant units.
4. Understand what the query is actually asking for.
5. Turn evidence into a grounded answer.
6. Connect information that lives in different sessions.
7. Prove any of it works.

The hard, distinctive core is **#6 layered on #5: cross-session, compositional,
grounded question answering.** Everything else is plumbing in service of that.

The mentor's example proves it: *"I earn £800, rent £400, food £100, travel 5
days — make a plan."* Almost none of that is a retrieval problem. It is
(a) pulling structured facts out of language, (b) possibly fetching facts the
user did not restate from earlier sessions, and (c) reasoning over them. Tuning
the snippet retriever does nothing for any of those three.

---

## 2. Layer 1 — Recovering structure from the PDF

A PDF is a visual projection of structured data; roles, turns and order were
discarded on export and must be reconstructed.

Options:
- **Geometry heuristic (current):** x-position decides role. Cheap, but
  format-specific and the least defensible code in the repo. Single-column
  exports break it entirely.
- **Marker/label parsing:** segment on real cues ("You" / "ChatGPT" headers,
  role labels, timestamps). Robust for the genre we actually have; explainable.
- **Ingest the structured source:** chat apps can export JSON/HTML/Markdown that
  keep roles losslessly. If allowed, half this problem disappears.
- **LLM-as-parser:** flexible, format-agnostic, but a black box that can invent
  structure. Weak on explainability.
- **Layout-ML (LayoutLM-style):** powerful, heavy, overkill for an MVP.

Choice: the input genre is narrow (AI chat exports), so a **marker-based parser
tuned to the formats we actually hold**, with geometry demoted to a last-resort
fallback. Design the parser from the data we have, not a guessed threshold —
so the first step is to open the real PDFs and see what cues they contain.

---

## 3. Layer 2 — Chunking (the unit of memory)

The granularity trade-off: too large dilutes embeddings and hurts precision;
too small loses context (a follow-up like "and the rent?" is meaningless alone).

Options: fixed token windows; turn / Q-A-pair chunking (conversation-aware);
sliding window over turns (current); topic-segmented chunking; or
**hierarchical / multi-granularity** (index at turn, session, and summary level).

Insight: the right granularity is dictated by the query type, so this layer
cannot be settled in isolation — factual recall wants a small tight unit, while
"summarise my month" wants a session-level or derived unit.

---

## 4. Layers 3 + 6 — Retrieval and the cross-session problem (the heart)

Structural truth most tutorials skip: **top-k vector search is biased toward
redundancy and single-aspect relevance.** It returns the k items most similar to
the query string. For a compositional question, the needed facts (income, rent,
food, transport) are spread across sessions, each only weakly similar to the
whole query, and get crowded out by near-duplicates. So pure dense retrieval
cannot reliably assemble the complementary set a compositional answer needs.
More k, dedup and diversification soften this but do not fix it — they are all
still bound to query-similarity.

Options to genuinely connect across sessions:
- **Query decomposition / multi-hop:** split the query into sub-questions,
  retrieve each, then compose. Directly attacks compositionality.
- **Derived structured memory (the big one):** extract facts once into a
  normalized per-user store — a fact store (income=800, rent=400...), session
  summaries, a profile. A planning query becomes a lookup/join, not a retrieval
  gamble. The cross-session problem largely dissolves.
- **Entity / knowledge-graph memory:** most powerful for linking, heaviest to
  build and justify. A "if we went further" option, not for the MVP.
- **Agentic iterative retrieval:** an LLM decides what to fetch next. Powerful
  but a black box and hard to bound.

**Key reframe:** the project's headline capability lives in the derived-memory
layer the code does not have yet. Session summaries / fact memory / profile are
not a future nicety — they are the brain. The snippet retriever is plumbing.
The hardcoded `answer_burger_query` and `generate_profile_answer` functions exist
precisely as a fake stand-in for this missing layer: they hardcode the outputs a
real fact/profile store would produce. Removing them forces the honest admission
that the memory layer must be built for real.

Separate sub-skill: the constraints (£800, £400, "5 days") are supplied in the
query itself, so **constraint extraction from natural language** is its own
problem, parallel to retrieval (LLM with structured output is the clean route).

---

## 5. Layer 4 — Intent understanding and routing

Different query types need different pipelines: factual recall, summarisation,
profile synthesis, planning, comparison, follow-up. The current keyword
heuristics are brittle (e.g. "tell me about machine learning" is misclassified
as a profile question).

Options: rules/keywords (transparent, brittle); a small trained classifier
(robust, needs labels); LLM zero/few-shot with structured output (flexible);
hybrid (cheap rules for greetings, LLM for the rest).

The part people skip is the **routing table**: for each intent, what concretely
changes downstream — which chunk granularity, which retrieval strategy, which
generation mode? Classifying intent and then doing the same thing regardless is
a common and useless outcome. Defining "intent X -> retrieval Y -> generation Z"
explicitly is the actual work.

---

## 6. Layer 5 — Grounded generation

Human-like answers need an LLM that reasons and composes, not snippet-dumping.
The risk is hallucination beyond the evidence.

Options: pure templates (faithful, dumb); LLM grounded in retrieved snippets with
a strict contract ("use only this evidence, cite the session, say you don't know
if unsupported"); or LLM reasoning over the structured intermediate (the fact
store) rather than raw text — which planning/compositional answers actually need.

Defensibility comes not from the LLM but from constraining it to evidence and
showing that evidence in the UI. The key fork — raw snippets vs structured state
— is decided by intent: recall/summary -> snippets; planning -> structured state.

---

## 7. Layer 7 — How do we know it works?

The project currently has no evaluation, so "works" cannot be distinguished from
"looked good in one demo." This is the most important missing piece and the thing
that makes "tackle all edge cases" concrete.

Needs:
- A small **gold set**: 15–20 queries across every intent, each with the expected
  answer and the expected supporting evidence.
- Two separate metrics: **retrieval quality** (did the right session/snippet
  surface?) and **answer faithfulness** (is every claim backed by evidence?).
- An explicit **edge-case catalogue**: empty PDF; single-column export with no
  role markers; a question about information not in any session; conflicting facts
  across two sessions; a follow-up depending on the previous turn; a query mixing
  supplied constraints with stored ones.

---

## 8. What broad thinking buys us

- **A defensible narrative:** multi-stage problem; the hard part is cross-session
  compositional grounding; the snippet retriever is plumbing; the real
  intelligence is a derived-memory layer; and here is how we measure it.
- **A re-prioritised build:** canned functions out, memory layer in, magic numbers
  either justified or moved to config.
- **A reason behind every change**, which is the whole point.

Build order is tracked in CLAUDE.md.
