import os
import sys
import uuid
import streamlit as st
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except (st.errors.StreamlitSecretNotFoundError, KeyError):
    pass 

from app.services.ingestion import process_document
from app.services.embeddings import embed_chunks
from app.services.vectorstore import add_chunks, query_chunks
from app.services.llm import get_answer

st.set_page_config(page_title="ragdocs", page_icon="📄", layout="centered")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; }
    .block-container { padding-top: 2rem; max-width: 800px; }
    [data-testid="stChatMessage"] { padding: 0.5rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "document_id" not in st.session_state:
    st.session_state.document_id = None
if "filename" not in st.session_state:
    st.session_state.filename = None
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📄 ragdocs")
st.caption("Upload a PDF and ask questions about it — answers are grounded in the document's actual content.")

with st.sidebar:
    st.header("Document")

    if st.session_state.document_id is None:
        uploaded_file = st.file_uploader("Upload a PDF", type="pdf")

        if uploaded_file is not None:
            if not uploaded_file.name.lower().endswith(".pdf"):
                st.error("Only PDF files are supported.")
            else:
                with st.spinner("Reading and indexing document... this can take a minute for large files"):
                    document_id = str(uuid.uuid4())
                    file_path = f"data/uploads/{uploaded_file.name}"

                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    try:
                        chunks = process_document(file_path)

                        if len(chunks) == 0:
                            st.error("No readable text found in this PDF. It may be scanned/image-only.")
                        else:
                            chunks = embed_chunks(chunks)
                            add_chunks(chunks, document_id)
                            st.session_state.document_id = document_id
                            st.session_state.filename = uploaded_file.name
                            st.rerun()
                    except Exception as e:
                        st.error(f"Something went wrong processing this file: {e}")
    else:
        st.success(f"📎 {st.session_state.filename}")
        if st.button("Upload a different document"):
            st.session_state.document_id = None
            st.session_state.filename = None
            st.session_state.messages = []
            st.rerun()

if st.session_state.document_id is None:
    st.info("👈 Upload a PDF from the sidebar to get started.")
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("View sources"):
                    for s in msg["sources"]:
                        st.caption(f"Page {s['page']} · distance {s['distance']:.3f}")
                        st.write(s["text"][:300] + "...")

    question = st.chat_input("Ask a question about the document")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    matches = query_chunks(question, st.session_state.document_id)

                    if len(matches) == 0:
                        st.error("No document found. Please upload a document first.")
                        st.stop()

                    answer = get_answer(question, matches)
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
                    st.stop()

            st.write(answer)
            with st.expander("View sources"):
                for s in matches:
                    st.caption(f"Page {s['page']} · distance {s['distance']:.3f}")
                    st.write(s["text"][:300] + "...")

        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": matches})