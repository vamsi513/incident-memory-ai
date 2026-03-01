import os

import streamlit as st
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")


st.set_page_config(page_title="IncidentMemory AI", layout="wide")

st.title("IncidentMemory AI")
st.caption("Operational memory for incidents, runbooks, GitHub issues, and engineering docs")

if "history" not in st.session_state:
    st.session_state.history = []

query = st.text_input("Ask a question about past incidents")

if st.button("Ask") and query.strip():
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        st.session_state.history.append(
            {
                "query": query,
                "answer": data["answer"],
                "citations": data["citations"],
                "retrieved_chunks": data["retrieved_chunks"],
            }
        )
    except Exception as exc:
        st.error(f"Request failed: {exc}")

for item in reversed(st.session_state.history):
    st.markdown("---")
    st.subheader(f"Question: {item['query']}")
    st.write(item["answer"])

    st.markdown("**Citations**")
    for citation in item["citations"]:
        st.write(f"- {citation}")

    with st.expander("Retrieved Chunks"):
        for idx, chunk in enumerate(item["retrieved_chunks"], start=1):
            st.markdown(f"**[{idx}] {chunk['title']} | {chunk['section']}**")
            st.write(chunk["text"])
            st.caption(f"path: {chunk.get('path')} | source: {chunk.get('source')}")

