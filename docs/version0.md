# Version 0 — Multi-Session Conversational RAG Prototype

## 1. Overview

Version 0 is the first working prototype of the project. Its purpose is to demonstrate an end-to-end Retrieval-Augmented Generation pipeline for conversational data stored across multiple PDF sessions.

Each PDF represents one day of conversation between a user and an AI assistant. The system ingests these PDFs, processes them into retrievable snippets, stores them in a vector database, retrieves relevant snippets for a new query, and produces a grounded answer with visible supporting evidence.

This version proves that the core multi-session retrieval workflow works.

---

## 2. Problem Being Solved

A normal chat session only has access to its own local context. It does not automatically know what happened in other sessions, even if those sessions belong to the same user.

Because of this, useful information from previous conversations is lost unless it is manually repeated.

Version 0 addresses this by creating a searchable memory layer across sessions:
- ingest previous conversation PDFs
- convert them into semantic memory
- retrieve relevant snippets across sessions
- answer using those snippets as context

---

## 3. Core Features Implemented

### 3.1 PDF Ingestion
The system accepts PDF files as input, where each file is treated as a separate conversation session.

### 3.2 Text / Block Extraction
PDF content is extracted using block-level extraction so that layout information can be used where necessary.

### 3.3 Conversation Parsing
Extracted blocks are cleaned and parsed into conversation-like turns using heuristic role inference.

### 3.4 Snippet Chunking
Parsed turns are grouped into overlapping snippets to preserve context while keeping retrieval precise.

### 3.5 Embedding Generation
Each snippet is converted into a semantic embedding using a sentence embedding model.

### 3.6 Vector Database Storage
Embeddings and associated metadata are stored in a vector database for semantic search.

### 3.7 Top-k Retrieval
For each user query, the system retrieves the top relevant snippets from indexed sessions.

### 3.8 Evidence-backed Answering
The UI displays:
- the final answer
- the retrieved supporting snippets
- session identifiers
- retrieval scores

### 3.9 Basic UI
A Streamlit-based interface supports:
- PDF upload
- indexing
- per-file processing visibility
- querying
- evidence inspection

---

## 4. Architecture of Version 0

```text
PDF files
   ↓
Extraction
   ↓
Parsing
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Database
   ↓
User Query
   ↓
Query Embedding
   ↓
Retrieval
   ↓
Fallback Answer Generation
   ↓
UI with Supporting Evidence