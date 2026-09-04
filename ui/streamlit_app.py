import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

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
            with st.spinner("Reading and indexing document... this can take a minute for large files"):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

                try:
                    response = requests.post(f"{API_URL}/upload", files=files, timeout=120)
                except requests.exceptions.ConnectionError:
                    st.error("Can't reach the backend. Is the FastAPI server running?")
                    st.stop()
                except requests.exceptions.Timeout:
                    st.error("The request timed out. The document may be too large.")
                    st.stop()
                else:
                    if response.status_code != 200:
                        st.error(response.json()["detail"])
                    else:
                        data = response.json()
                        st.session_state.document_id = data["document_id"]
                        st.session_state.filename = data["filename"]
                        st.rerun()
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
                    response = requests.post(
                        f"{API_URL}/chat",
                        params={"question": question, "document_id": st.session_state.document_id},
                        timeout=60,
                    )
                except requests.exceptions.ConnectionError:
                    st.error("Can't reach the backend. Is the FastAPI server running?")
                    st.stop()
                except requests.exceptions.Timeout:
                    st.error("The request timed out.")
                    st.stop()
                else:
                    if response.status_code != 200:
                        st.error(response.json()["detail"])
                        st.stop()
                    else:
                        data = response.json()
                        answer = data["answer"]
                        sources = data["sources"]

            st.write(answer)
            with st.expander("View sources"):
                for s in sources:
                    st.caption(f"Page {s['page']} · distance {s['distance']:.3f}")
                    st.write(s["text"][:300] + "...")

        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})