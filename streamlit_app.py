"""
Voice Doc Agent — Web Version

A shareable web front-end for the voice document agent. Visitors upload
their own document and talk to it (voice or text), fully isolated per
browser session — no crosstalk between users.

Run locally:
    streamlit run streamlit_app.py

Deploy: push to GitHub, connect at https://share.streamlit.io
"""

import os
import tempfile
from pathlib import Path

import streamlit as st
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv

from app.loaders import load_document
from app.chunker import chunk_documents
from app.indexer import get_or_build_index
from app.qa_chain import query_document
from app.voice_io import transcribe_audio, generate_speech_bytes
from app.web_fallback import search_web_for_answer

load_dotenv()

MAX_FILE_SIZE_MB = 15
MAX_QUESTIONS_PER_SESSION = 30

st.set_page_config(page_title="Talk to Your Document", page_icon="🎙️", layout="centered")


def get_secret(name: str, env_fallback: str = None) -> str:
    """Read from Streamlit secrets first, falling back to an env var (for local dev)."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(env_fallback or name, "")


def check_password() -> bool:
    """Simple shared-password gate. Returns True once the correct password is entered."""
    app_password = get_secret("APP_PASSWORD")

    if not app_password:
        # No password configured (e.g. local dev without secrets set) — allow through
        return True

    if st.session_state.get("authenticated"):
        return True

    st.title("🎙️ Talk to Your Document")
    st.write("This app is password-protected. Ask the owner for access.")
    entered = st.text_input("Password", type="password")

    if entered:
        if entered == app_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    return False


def init_session_state():
    defaults = {
        "vector_store": None,
        "doc_name": None,
        "chat_history": [],
        "question_count": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def handle_upload(uploaded_file):
    """Load, chunk, and index an uploaded document. Cached per session by filename+size."""
    doc_key = f"{uploaded_file.name}_{uploaded_file.size}"

    if st.session_state.get("doc_key") == doc_key:
        return  # Already indexed this exact upload in this session

    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File too large ({size_mb:.1f} MB). Max size is {MAX_FILE_SIZE_MB} MB.")
        return

    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        with st.spinner(f"Reading and indexing {uploaded_file.name}..."):
            documents = load_document(tmp_path)
            chunks = chunk_documents(documents)
            vector_store = get_or_build_index(tmp_path, chunks)

        st.session_state.vector_store = vector_store
        st.session_state.doc_name = uploaded_file.name
        st.session_state.doc_key = doc_key
        st.session_state.chat_history = []
        st.success(f"Ready! Ask me anything about **{uploaded_file.name}**.")
    except (FileNotFoundError, ValueError) as e:
        st.error(str(e))
    finally:
        os.unlink(tmp_path)


def ask_question(question: str):
    """Run the grounded RAG query and append the exchange to chat history."""
    if st.session_state.question_count >= MAX_QUESTIONS_PER_SESSION:
        st.warning(
            f"You've reached the {MAX_QUESTIONS_PER_SESSION}-question limit for this session. "
            "Refresh the page to start a new session."
        )
        return

    st.session_state.question_count += 1
    threshold = float(get_secret("RELEVANCE_THRESHOLD", "RELEVANCE_THRESHOLD") or 0.5)

    try:
        with st.spinner("Searching the document..."):
            answer, found, sources = query_document(
                st.session_state.vector_store, question, threshold=threshold
            )
    except Exception as e:
        st.session_state.chat_history.append(
            {"question": question, "answer": f"⚠ Error: {e}", "found": False, "sources": []}
        )
        return

    st.session_state.chat_history.append(
        {"question": question, "answer": answer, "found": found, "sources": sources}
    )


def render_chat_history():
    tts_voice = get_secret("TTS_VOICE", "TTS_VOICE") or "alloy"

    for i, turn in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(turn["question"])

        with st.chat_message("assistant"):
            st.write(turn["answer"])

            if turn["found"] and turn["sources"]:
                with st.expander("Sources"):
                    for src in turn["sources"]:
                        st.caption(f"Page {src['page']}: {src['content']}")

            # Play answer as speech
            audio_key = f"audio_{i}"
            if audio_key not in st.session_state:
                try:
                    st.session_state[audio_key] = generate_speech_bytes(turn["answer"], voice=tts_voice)
                except Exception as e:
                    print(f"TTS failed: {e}", file=__import__('sys').stderr)
                    st.session_state[audio_key] = b""
                    st.caption("🔇 Audio unavailable")
            if st.session_state[audio_key]:
                st.audio(st.session_state[audio_key], format="audio/mp3", autoplay=True)

            # Web fallback offer (only on the most recent not-found turn)
            if not turn["found"] and i == len(st.session_state.chat_history) - 1:
                if st.button("🌐 Search the web instead", key=f"web_fallback_{i}"):
                    with st.spinner("Searching the web..."):
                        web_answer = search_web_for_answer(turn["question"])
                    st.info(web_answer)
                    try:
                        web_audio = generate_speech_bytes(web_answer, voice=tts_voice)
                        if web_audio:
                            st.audio(web_audio, format="audio/mp3", autoplay=True)
                    except Exception as e:
                        print(f"Web fallback TTS failed: {e}", file=__import__('sys').stderr)
                        st.caption("🔇 Audio unavailable for web result")


def main():
    if not check_password():
        return

    init_session_state()

    st.title("🎙️ Talk to Your Document")
    st.caption("Upload a document (PDF, DOCX, or TXT) and ask it questions — by voice or text.")

    if not get_secret("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is not configured. The app owner needs to set this secret.")
        return

    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])
    if uploaded_file:
        handle_upload(uploaded_file)

    if st.session_state.vector_store is None:
        st.info("👆 Upload a document to get started.")
        return

    st.divider()
    st.caption(
        f"Talking to: **{st.session_state.doc_name}** · "
        f"{st.session_state.question_count}/{MAX_QUESTIONS_PER_SESSION} questions used this session"
    )

    render_chat_history()

    col1, col2 = st.columns([4, 1])
    with col1:
        text_question = st.chat_input("Type your question...")
    with col2:
        audio_bytes = audio_recorder(text="🎤", icon_size="2x", key="recorder")

    if text_question:
        ask_question(text_question)
        st.rerun()

    if audio_bytes:
        recorder_key = f"last_audio_len_{len(audio_bytes)}"
        if st.session_state.get("last_processed_audio") != recorder_key:
            st.session_state["last_processed_audio"] = recorder_key
            try:
                with st.spinner("Transcribing..."):
                    question = transcribe_audio(audio_bytes)
                ask_question(question)
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))


if __name__ == "__main__":
    main()
