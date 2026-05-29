
---

# `docs/version_1_plan.md`

```md
# Version 1 Plan — Refactored, Intent-Aware, LLM-Backed RAG System

## 1. Goal of Version 1

Version 1 is the next phase of the project. Its purpose is to move from a working prototype to a more polished, explainable, and intelligent conversational RAG system.

The focus of Version 1 is not just retrieval, but:
- cleaner architecture
- stronger UI
- LLM-backed answer generation
- intent-aware orchestration
- better user-facing behavior

---

## 2. Why Version 1 Is Needed

Version 0 proves the pipeline works, but it still behaves like a prototype:
- retrieval quality depends too heavily on clean input
- answer generation is limited
- broad or intent-heavy queries are not handled well
- the UI still looks like a technical demo
- some logic is still heuristic and scattered

Version 1 is needed to make the system:
- easier to explain
- easier to maintain
- more useful for real query handling
- more aligned with the actual project vision

---

## 3. Main Objectives of Version 1

### 3.1 Refactor the Codebase
The codebase should be cleaned so that:
- no unnecessary code remains
- duplicated logic is removed
- each file has a clearly defined role
- orchestration is easier to follow

### 3.2 Introduce an LLM Layer
The final answer should no longer depend only on fallback formatting.
Instead:
- retrieved snippets should be passed to an LLM
- the LLM should generate the final answer
- the response should remain grounded in retrieved evidence

### 3.3 Add Intent-Aware Query Handling
The system should not treat all queries the same.
It should detect whether a query is:
- factual recall
- summarization
- profile/about-me
- planning/advice
- comparison
- greeting/small talk

### 3.4 Improve the UI
The interface should visually explain the project without requiring spoken explanation.
A new user or evaluator should understand:
- what is uploaded
- what is indexed
- what is retrieved
- how the final answer is generated

### 3.5 Improve Cross-Session Behavior
The system should better handle queries that require:
- combining information from multiple sessions
- understanding the user’s broader context
- going beyond topic matching into intent matching

---

## 4. Proposed Version 1 Architecture

```text
Uploaded Session PDFs
        ↓
Extraction Layer
        ↓
Parsing Layer
        ↓
Chunking Layer
        ↓
Embedding Layer
        ↓
Vector Database
        ↓
User Query
        ↓
Intent Detection
        ↓
Query Rewriting / Routing
        ↓
Candidate Retrieval
        ↓
Reranking / Session Diversification
        ↓
LLM-based Response Generation
        ↓
UI with Evidence + Reasoning View