import os
import tempfile
import streamlit as st

from src.pipeline import process_pdf_file, summarize_ingestion
from src.retriever import retrieve_top_k
from src.generator import generate_answer
from src.vectordb import close_client

st.set_page_config(page_title="Multi-Session Conversational RAG", layout="wide")

st.title("Multi-Session Conversational RAG Module")
st.markdown(
    """
This prototype ingests conversation PDFs across multiple sessions, indexes them into a vector database,
retrieves the top 3 most relevant snippets for a new query, and uses them as grounded context for answering.
"""
)

# -------------------------
# Session state
# -------------------------
if "ingestion_results" not in st.session_state:
    st.session_state.ingestion_results = []

if "ingestion_summary" not in st.session_state:
    st.session_state.ingestion_summary = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# -------------------------
# Sidebar: Upload + indexing
# -------------------------
st.sidebar.header("Session Upload & Indexing")

uploaded_files = st.sidebar.file_uploader(
    "Upload conversation PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

index_clicked = st.sidebar.button("Index Sessions")

if index_clicked:
    if not uploaded_files:
        st.sidebar.warning("Please upload at least one PDF file.")
    else:
        results = []

        with st.spinner("Processing and indexing uploaded sessions..."):
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name

                result = process_pdf_file(
                    file_path=tmp_path,
                    original_name=uploaded_file.name
                )
                results.append(result)

                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        st.session_state.ingestion_results = results
        st.session_state.ingestion_summary = summarize_ingestion(results)

        close_client()


# -------------------------
# Main area: Ingestion summary
# -------------------------
st.subheader("1. Ingestion Pipeline Status")

if st.session_state.ingestion_summary:
    summary = st.session_state.ingestion_summary

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Files Uploaded", summary["total_files"])
    col2.metric("Indexed Successfully", summary["success_count"])
    col3.metric("Total Turns Parsed", summary["total_turns"])
    col4.metric("Total Snippets Created", summary["total_snippets"])

    st.markdown("### Per-file Processing Results")

    for result in st.session_state.ingestion_results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        with st.expander(f"{status_icon} {result['file_name']} — {result['status'].upper()}"):
            st.write(f"**Session ID:** {result['session_id']}")
            st.write(f"**Blocks Extracted:** {result['blocks_extracted']}")
            st.write(f"**Turns Parsed:** {result['turns_parsed']}")
            st.write(f"**Snippets Created:** {result['snippets_created']}")
            st.write(f"**Stored in Vector DB:** {result['stored']}")
            if result["reason"]:
                st.write(f"**Reason:** {result['reason']}")
else:
    st.info("No sessions indexed yet. Upload PDFs from the sidebar and click 'Index Sessions'.")


# -------------------------
# Query section
# -------------------------
st.subheader("2. Query the Indexed Sessions")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Ask something about the indexed sessions")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    docs = retrieve_top_k(query, k=3)
    answer = generate_answer(query, docs)

    with st.chat_message("assistant"):
        st.markdown("### Final Answer")
        st.markdown(answer)

        with st.expander("Retrieved Evidence (Top 3 Snippets)", expanded=True):
            if docs:
                for i, doc in enumerate(docs, start=1):
                    st.markdown(
                        f"**{i}. Session:** {doc['session_id']} | "
                        f"**Turns:** {doc['turn_start']}-{doc['turn_end']} | "
                        f"**Score:** {doc['score']:.4f}"
                    )
                    st.code(doc["text"])
            else:
                st.warning("No relevant snippets were retrieved.")

    st.session_state.messages.append({"role": "assistant", "content": answer})