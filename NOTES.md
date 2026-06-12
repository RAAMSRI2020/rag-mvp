What changed and why

src/intent.py (created)

- is_small_talk and is_profile_query — copied verbatim from both files. The bodies are identical in both originals, so there is one canonical version to copy; no judgement call needed.
- rewrite_query_if_needed — moved from retriever.py only. It is pure intent logic (it looks at what the query means and transforms it), not retrieval logic. It belongs here, not in a file about searching a vector DB.
- analyze_query — new function, four lines. It calls the three helpers in priority order and returns a string label. Nothing calls it yet; it is the scaffolding that Stage 2 will use when pipeline.py needs a single entry point for intent. Its logic is trivially derivable from the three helpers — no new decisions are introduced.

src/retriever.py (edited)

- Added one import: from src.intent import is_small_talk, is_profile_query, rewrite_query_if_needed. This is why retriever.py still works — Python now resolves those names from intent.py instead of locally.
- Deleted the three local definitions. Every call site (is_small_talk at line 22, rewrite_query_if_needed at line 25, is_profile_query at line 53) is untouched. Same call, different resolution path — identical runtime behaviour.

src/generator.py (edited)

- Added one import: from src.intent import is_small_talk, is_profile_query.
- Deleted the two local definitions. Same reasoning: call sites at lines 225 and 241 are untouched.

---
Why this approach over alternatives: The alternative would have been to have retriever.py and generator.py call analyze_query() instead of the individual helpers. That would also be clean, but it changes the call sites and therefore the observable code path — not allowed in Stage 1. Keeping the individual functions exported from intent.py means zero call-site changes, which is the safest possible Stage 1.