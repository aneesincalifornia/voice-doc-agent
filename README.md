# Voice Doc Agent — Talk to Your Documents

Ask questions to any document (PDF, DOCX, TXT, or Excel) using your voice. Get answers back as both text and speech. Grounded entirely in the document — no hallucinations. Email yourself the conversation transcript when you're done.

## Features

- **Voice or text input** — speak a question (mic) or type it
- **Document grounding** — answers come ONLY from your document, never guesses
- **Web fallback** — if the answer isn't found, optionally search the web (clearly labeled)
- **Speech output** — answers are spoken back to you via TTS
- **Multiple formats** — PDF, DOCX, TXT, or Excel (.xlsx with multiple sheets)
- **Email transcripts** — save your conversation history to email at the end of a session
- **Cached indexing** — repeated questions don't re-embed (saves API cost)
- **Robust error handling** — gracefully falls back if mic is unavailable

## Setup

```bash
# Clone or navigate to the project
cd voice_doc_agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy .env.example and add your key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

```bash
# Ask about a specific document
python voice_agent.py path/to/your/document.pdf

# Or prompt for the path
python voice_agent.py

# Once running:
#   - Press Enter to start speaking (or Enter to stop)
#   - Type a question directly
#   - Type 'exit' to quit
```

### Example

```
$ python voice_agent.py data/employee_handbook.pdf

📄 Loading document: data/employee_handbook.pdf
✓ Loaded 12 pages from PDF
✓ Created 34 chunks from 12 document(s)
✓ Loading cached index from indexes/abc123def456...

Ready! Ask me about the document.
Commands: Press Enter to speak, or type a question, or 'exit'

[Enter to speak, or type a question]: How many days of leave do employees get?

🔍 Searching document...

📝 Answer:
Employees are entitled to 20 days of annual leave per year, which must be taken
in agreement with their manager.

📚 Sources:
  Page 3: Leave Policy section states that annual leave entitlements are...
```

## Configuration

Edit `.env` to customize. Copy from `.env.example` for a template:

```env
# OpenAI API (required)
OPENAI_API_KEY=sk-your-key-here
CHAT_MODEL=gpt-4o-mini              # LLM for Q&A
EMBED_MODEL=text-embedding-3-small  # Embedding model

# Voice settings (optional)
TTS_VOICE=alloy                     # Speech output voice (alloy, echo, fable, onyx, nova, shimmer)
RELEVANCE_THRESHOLD=0.5             # Similarity threshold for "not found" (0-1)

# Email settings (optional - only needed to email transcripts)
# For Gmail: use an app password, not your regular password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password-here
```

**To generate a Gmail app password:**
1. Enable 2-factor authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer" (or your device)
4. Copy the generated 16-character password
5. Paste it into `SMTP_PASSWORD` in `.env`

## Architecture

```
Document (PDF/DOCX/TXT/Excel)
   ↓
Loader (format-specific extraction)
   ↓
Chunker (RecursiveCharacterTextSplitter)
   ↓
Embeddings (OpenAI text-embedding-3-small)
   ↓
FAISS Index (cached by file hash)
   ↓
Query → Retriever + Threshold Check
   ↓
If relevant: Grounded LLM (only uses retrieved context)
   ↓
Answer + TTS + on-screen text
   ↓
If not found: Optional web fallback (clearly labeled)
   ↓
On exit: Optional email transcript (SMTP)
```

## Testing

```bash
# Run all tests (mocked OpenAI calls, no API cost)
pytest -v

# Run a specific test file
pytest tests/test_qa_chain.py -v

# Run with coverage
pytest --cov=app tests/
```

Test suite includes:
- `test_loaders.py` — PDF/DOCX/TXT/Excel loading, error handling
- `test_chunker.py` — text splitting with overlap
- `test_indexer.py` — index caching, build/load roundtrips
- `test_qa_chain.py` — document grounding, threshold logic
- `test_voice_io.py` — transcription, speech output, mic detection
- `test_emailer.py` — SMTP email sending, credential validation
- `test_web_fallback.py` — web search with labeling
- `test_integration.py` — end-to-end pipeline

Total: 58 tests, all mocked (no API cost)

## Robustness Notes

- **No API key** → fails at startup with clear message
- **Unsupported file type** → clear error before indexing
- **No mic available** → automatically falls back to text-only mode
- **API errors** → retries with backoff, then shows friendly error
- **Irrelevant query** → returns "not found" without calling LLM (cheaper, prevents hallucination)
- **Empty transcription** → reprompts instead of sending empty question to LLM

## How It Works

### Document Grounding

The agent uses **strict prompt engineering** + **relevance thresholding**:

1. User question is converted to embeddings
2. Top-k chunks are retrieved from FAISS
3. If the best match has a low similarity score (below threshold), the agent returns "No such information found in the document." without calling the LLM — this prevents hallucination on clearly-irrelevant queries and saves API cost
4. If the match is good, the question + retrieved chunks are sent to GPT with a prompt that says:
   - **Use ONLY the provided context**
   - **If the answer isn't there, reply with exactly: "No such information found in the document."**
   - **Do not guess or use general knowledge**
5. The response is parsed: if the LLM's answer contains the sentinel phrase, `found=False` and web fallback is offered

### Web Fallback

When `found=False` and the user opts in, the agent calls OpenAI's web search capability with the question. The result is always prefixed `[From the web, not your document]:` so it's never confused with document-grounded answers.

## Voice Tech Stack

- **Speech-to-text**: OpenAI Whisper (via `sounddevice` + `scipy` for mic recording)
- **Text-to-speech**: OpenAI TTS (via `afplay` on macOS)
- **LLM**: OpenAI GPT-4o-mini (configurable)
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: FAISS (in-memory, cached to disk)

## Limitations & Future Work

### Current (v1)
- Single-user, local CLI (no backend API yet)
- Mic recording works on macOS (uses `afplay`); other OSes need playback adaptation
- No persistent chat history (each query is independent)
- Web fallback uses Responses API (requires web-search-enabled account)

### Future
- **Frontend**: Streamlit or React + FastAPI backend for web UI
- **Multi-user**: session/document isolation for concurrent users
- **Persistent indexing**: upload documents once, use across sessions
- **RAG improvements**: hybrid search (BM25 + semantic), multi-hop reasoning
- **Audio improvements**: streaming TTS, better mic handling

## License

MIT

## Author

Built with ❤️ by Anees Fatima

---

## Quick Troubleshooting

**"OPENAI_API_KEY not set"**
→ Create `.env` file with `OPENAI_API_KEY=sk-...`

**"No microphone detected"**
→ Agent falls back to text mode automatically. Just type your questions.

**"afplay not found"**
→ You're not on macOS. Modify `voice_io.py` to use your OS's audio player (e.g., `paplay` on Linux).

**"No such information found"**
→ The document doesn't contain the answer. Rephrase or search the web (press 'y' at the prompt).

**Tests failing with "mocked OpenAI"**
→ Tests use mocked API calls, so API key isn't checked. Run `pytest -v` to see details.
