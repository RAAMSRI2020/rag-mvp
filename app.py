import streamlit as st

from src.retriever import retrieve_top_k
from src.generator import build_answer

st.set_page_config(page_title="RAG Chatbot MVP", layout="wide")
st.title("Multi-Session Conversation RAG")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

query = st.chat_input("Ask something about the stored conversations")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    docs = retrieve_top_k(query, k=3)
    answer = build_answer(query, docs)

    with st.chat_message("assistant"):
        st.markdown(answer)

        st.markdown("### Top 3 Retrieved Snippets")
        for i, doc in enumerate(docs, start=1):
            st.markdown(
                f"**{i}. Session:** {doc['session_id']} | "
                f"**Turns:** {doc['turn_start']}-{doc['turn_end']} | "
                f"**Score:** {doc['score']:.4f}"
            )
            st.code(doc["text"])

    st.session_state.messages.append({"role": "assistant", "content": answer})