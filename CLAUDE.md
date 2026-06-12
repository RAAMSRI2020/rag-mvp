# CLAUDE.md — rag-mvp

Project memory for Claude Code. Read this fully at the start of every session.

## What this project is
An intent-aware conversational RAG system that answers questions from uploaded
chat-history PDFs. The aim is human-like answers: understand intent, connect
information across multiple sessions, reason over evidence, and stay grounded.
Today the system is semantic search + snippet display with heuristic routing.
It is NOT yet intent-aware, has no LLM, and has no cross-session memory.

## Working branch
All work happens on `rag-mvp-v3`. The `main` branch is an old prototype; ignore it.

## Golden rules (these come from my mentor — never break them)
1. **Explainability test.** If I cannot explain why a piece of code is here and
   why it works, it does not belong in the project. Delete unexplainable code.
2. **No overfit / demo-rigged code.** No hardcoded answers tuned to specific
   sample PDFs. The system must answer generally from retrieved evidence.
3. **Bounded changes only.** One small, reviewable change per task and per commit.
   Never rewrite the repo. Every change must keep the project compiling and,
   unless the task says otherwise, preserve existing behaviour.
4. **Plan before editing.** Before touching files, state: the plan, the exact
   files to be touched, and why. Wait for my approval. Then edit.
5. **Teach, don't just type.** After each change, explain it line by line and
   explain why this approach over the alternatives. I write the commit message
   in my own words; if I can't, the change is not understood and does not ship.

## Current real state (v3) — what each file owns
- `app.py` — Streamlit UI. Currently also holds business logic (should become UI-only).
- `config.py` — constants: TOP_K=3, RETRIEVE_K=10, WINDOW_SIZE=4, OVERLAP=2,
  USER_X_THRESHOLD=150.0 (NOTE: parser ignores this and hardcodes its own 150.0).
- `ingest.py` — ingestion script; duplicates pipeline ingestion logic.
- `src/pdf_loader.py` — extracts text blocks from PDF (PyMuPDF).
- `src/parser.py` — cleans blocks, assigns roles by x-position (x0 >= 150 -> User),
  merges same-role turns. The role heuristic is the most fragile code in the repo.
- `src/chunker.py` — sliding window over turns (size 4, overlap 2).
- `src/embedder.py` — sentence-transformers all-MiniLM-L6-v2.
- `src/vectordb.py` — Qdrant: ensure_collection, upsert, search. Uses Python
  hash() for point IDs (unstable across processes — re-ingest can duplicate).
- `src/retriever.py` — dense search + lexical overlap + hybrid rerank (0.75/0.25)
  + dedup + profile diversification. Also contains duplicated intent helpers.
- `src/generator.py` — heuristic answer builder with hardcoded routes.
- `src/pipeline.py` — ingestion only (process_pdf_file, summarize_ingestion).

## Code triage (decided with prior analysis)
**Pile 1 — remove (overfit / indefensible):**
- `generator.py::answer_burger_query` — hardcoded burger knowledge for one PDF.
- `generator.py::generate_profile_answer` — keyword lists -> canned sentences.
- `generator.py::answer_topic_list_query` — `^Block \d+ — ...$` regex, one PDF only.
- `parser.py::clean_block_text` — sample-specific noise filters (e.g. ".pptx",
  hardcoded title lines).
- `pipeline.py::is_good_snippet` junk regex `𝒖:|𝒄:|FC`, `\bA'\b`, `\bco\b`
  (the last wrongly rejects any snippet containing the word "co").

**Pile 2 — justify or move to named config:**
- Magic numbers: parser 150.0; snippet len<80, symbol_ratio>0.20, words<15;
  hybrid weights 0.75/0.25; RETRIEVE_K=10; answer-quality cutoffs 0.45/0.30.
  Each must have a stated rationale or become a documented config value.

**Pile 3 — real bugs / edge cases to fix:**
- `is_profile_query` false-positive: "tell me about X" is misrouted to profile.
- Role-by-x-position fails on single-column exports (all turns collapse to one
  role). Needs a marker-based path and a safe fallback.
- `vectordb.py` hash()-based IDs are not stable; use a deterministic hash.
- `is_small_talk` / `is_profile_query` duplicated in retriever.py and generator.py.

## Build order (do in sequence, one commit each)
1. **Stage 1:** create `src/intent.py` owning `analyze_query()`; move the intent
   helpers there; retriever.py and generator.py import from it. Behaviour unchanged.
2. **Stage 2:** add `pipeline.answer_query(query)` (intent -> retrieve -> generate
   -> structured result {query, intent, docs, answer}); make app.py call it so
   app.py becomes UI-only.
3. Remove Pile 1 code; replace canned routes with general evidence-grounded answers.
4. Build the derived-memory layer (session summaries, fact store, profile) — this
   is the real intelligence, currently faked by the Pile 1 functions.
5. Constraint extraction from queries; intent routing table; grounded LLM answers.
6. Evaluation: a gold-set of queries + an explicit edge-case catalogue.

## Coding conventions
- Python, one job per module, clear ownership, no dead code.
- Prefer named, documented constants over inline magic numbers.
- Small functions; explicit returns; no silent failure (handle empty PDF, no
  role markers, query about absent information, conflicting facts).

## Definition of done for any task
- Compiles and runs; existing behaviour preserved unless the task changes it.
- I can explain every changed line and why the approach was chosen.
- Commit message written by me, in my own words.
- NOTES.md updated with what changed and why.
