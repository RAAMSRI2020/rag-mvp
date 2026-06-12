import os
import tempfile
import streamlit as st

from src.pipeline import process_pdf_file, summarize_ingestion, answer_query
from src.vectordb import close_client

st.set_page_config(page_title="Multi-Session Conversational RAG", layout="wide")
st.title("Multi-Session Conversational RAG Module")
st.caption(
    "Upload conversation PDFs, index them as searchable snippets, and answer new questions using retrieved cross-session context."
)

if "ingestion_results" not in st.session_state:
    st.session_state.ingestion_results = []
if "ingestion_summary" not in st.session_state:
    st.session_state.ingestion_summary = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
st.sidebar.header("Upload & Index Sessions")
uploaded_files = st.sidebar.file_uploader(
    "Upload conversation PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if st.sidebar.button("Index Sessions", use_container_width=True):
    if not uploaded_files:
        st.sidebar.warning("Upload at least one PDF.")
    else:
        results = []
        progress = st.sidebar.progress(0, text="Starting indexing...")

        for i, uploaded_file in enumerate(uploaded_files, start=1):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            result = process_pdf_file(tmp_path, uploaded_file.name)
            results.append(result)

            try:
                os.remove(tmp_path)
            except Exception:
                pass

            progress.progress(i / len(uploaded_files), text=f"Processed {i}/{len(uploaded_files)} files")

        st.session_state.ingestion_results = results
        st.session_state.ingestion_summary = summarize_ingestion(results)
        close_client()
        st.sidebar.success("Indexing complete.")

tab1, tab2 = st.tabs(["Ingestion Overview", "Ask the Sessions"])

with tab1:
    st.subheader("Indexed Session Status")

    if st.session_state.ingestion_summary:
        summary = st.session_state.ingestion_summary
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Files Uploaded", summary["total_files"])
        c2.metric("Indexed", summary["success_count"])
        c3.metric("Turns Parsed", summary["total_turns"])
        c4.metric("Snippets Stored", summary["total_snippets"])

        st.markdown("### Per-file Results")
        for result in st.session_state.ingestion_results:
            icon = "✅" if result["status"] == "success" else "❌"
            with st.expander(f"{icon} {result['file_name']}"):
                st.write(f"**Session ID:** {result['session_id']}")
                st.write(f"**Blocks Extracted:** {result['blocks_extracted']}")
                st.write(f"**Turns Parsed:** {result['turns_parsed']}")
                st.write(f"**Raw Snippets:** {result.get('raw_snippets_created', result['snippets_created'])}")
                st.write(f"**Stored Snippets:** {result['snippets_created']}")
                st.write(f"**Stored in Vector DB:** {result['stored']}")
                if result["reason"]:
                    st.write(f"**Reason:** {result['reason']}")
    else:
        st.info("Upload and index PDF sessions from the sidebar.")

with tab2:
    st.subheader("Query the Indexed Sessions")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    query = st.chat_input("Ask a specific question about the indexed conversations")

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        result = answer_query(query)
        docs = result["docs"]
        answer = result["answer"]

        with st.chat_message("assistant"):
            st.success("Answer generated from retrieved session context")
            st.markdown("### Final Answer")
            st.markdown(answer)

            if docs:
                st.markdown("### Supporting Evidence")
                for i, doc in enumerate(docs, start=1):
                    with st.expander(
                        f"#{i} | {doc['session_id']} | Hybrid {doc.get('hybrid_score', doc['score']):.4f}",
                        expanded=(i == 1)
                    ):
                        st.write(f"**Turns:** {doc['turn_start']}–{doc['turn_end']}")
                        st.write(f"**Dense score:** {doc['score']:.4f}")
                        if "lexical_score" in doc:
                            st.write(f"**Lexical score:** {doc['lexical_score']:.4f}")
                            st.write(f"**Hybrid score:** {doc['hybrid_score']:.4f}")
                        st.code(doc["text"])
            else:
                st.info("No supporting snippets were retrieved for this query.")

        st.session_state.messages.append({"role": "assistant", "content": answer})