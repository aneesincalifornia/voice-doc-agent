# Voice Doc Agent - Complete Project Structure

```
voice_doc_agent/
│
├── 📄 .env                          ⭐ YOUR API KEY GOES HERE
│   ├── OPENAI_API_KEY=sk-...       (Replace sk-your-key-here with your actual key)
│   ├── CHAT_MODEL=gpt-4o-mini      (LLM model)
│   ├── EMBED_MODEL=text-embedding-3-small
│   ├── TTS_VOICE=alloy             (Voice: alloy, echo, fable, onyx, nova, shimmer)
│   └── RELEVANCE_THRESHOLD=0.5     (Tune hallucination prevention)
│
├── 📄 .env.example                  (Template - don't edit, copy to .env)
├── 📄 .gitignore                    (Git ignore rules)
├── 📄 requirements.txt              (Python dependencies)
│
├── 📄 voice_agent.py ⭐ MAIN ENTRY POINT
│   └── Run with: python voice_agent.py data/sample_policy.txt
│
├── 📁 app/                          ⭐ CORE AGENT CODE
│   ├── __init__.py
│   │
│   ├── loaders.py                   (Load documents)
│   │   ├── load_document(path)      ← Main dispatcher function
│   │   ├── load_pdf()               ← PyPDFLoader
│   │   ├── load_docx()              ← python-docx
│   │   └── load_txt()               ← Plain text reader
│   │
│   ├── chunker.py                   (Split into chunks)
│   │   └── chunk_documents()        ← RecursiveCharacterTextSplitter
│   │       (chunk_size=1000, overlap=200)
│   │
│   ├── indexer.py                   (Build & cache FAISS indexes)
│   │   ├── get_file_hash()          ← SHA256 for caching
│   │   └── get_or_build_index()     ← Main indexing function
│   │       (checks cache, builds fresh if needed)
│   │
│   ├── qa_chain.py ⭐ GROUNDING LOGIC
│   │   └── query_document()         ← Main Q&A function
│   │       1. Retrieve top-k chunks (similarity search)
│   │       2. Check relevance threshold
│   │       3. If below threshold: return "not found" (no LLM call)
│   │       4. If above threshold: send to LLM with strict prompt
│   │       5. Parse response (check for sentinel phrase)
│   │       6. Return (answer, found: bool, sources: list)
│   │
│   ├── voice_io.py ⭐ VOICE FEATURES
│   │   ├── get_client()             ← Lazy OpenAI client init
│   │   ├── record_from_mic()        ← sounddevice + scipy
│   │   │   (Press Enter to start, Enter to stop)
│   │   ├── transcribe_audio()       ← OpenAI Whisper STT
│   │   ├── speak_response()         ← OpenAI TTS
│   │   │   (saved to temp MP3, played via afplay on macOS)
│   │   └── has_mic_available()      ← Check if mic exists
│   │
│   └── web_fallback.py              (Optional web search)
│       └── search_web_for_answer()  ← OpenAI web search
│           (Only called when found=False AND user opts in)
│           (Result always prefixed "[From the web, not your document]:")
│
├── 📁 tests/                        ⭐ 41 COMPREHENSIVE TESTS (All passing)
│   ├── __init__.py
│   ├── conftest.py                  (Shared fixtures & mocks)
│   │   ├── sample_text              (Employee leave policy text)
│   │   ├── temp_txt_file            (Temporary TXT file fixture)
│   │   ├── temp_pdf_file            (Temporary PDF file fixture)
│   │   └── mock_openai_key          (Mock API key for tests)
│   │
│   ├── test_loaders.py              (7 tests)
│   │   ├── test_load_txt_valid()
│   │   ├── test_load_txt_empty()
│   │   ├── test_load_document_txt()
│   │   ├── test_load_document_missing()
│   │   ├── test_load_document_unsupported()
│   │   ├── test_load_docx_missing()
│   │   └── test_load_document_via_dispatch()
│   │
│   ├── test_chunker.py              (5 tests)
│   │   ├── test_chunk_documents_basic()
│   │   ├── test_chunk_documents_preserves_metadata()
│   │   ├── test_chunk_documents_overlap()
│   │   ├── test_chunk_documents_empty()
│   │   └── test_chunk_documents_short()
│   │
│   ├── test_indexer.py              (5 tests)
│   │   ├── test_get_file_hash()
│   │   ├── test_get_file_hash_different_files()
│   │   ├── test_get_or_build_index_builds_fresh()
│   │   ├── test_get_or_build_index_loads_cached()
│   │   └── test_get_or_build_index_cache_dir_created()
│   │
│   ├── test_qa_chain.py             (5 tests) ← File you opened
│   │   ├── test_query_document_found()
│   │   ├── test_query_document_below_threshold()
│   │   ├── test_query_document_llm_returns_sentinel()
│   │   ├── test_query_document_empty_retrieval()
│   │   └── test_query_document_custom_threshold()
│   │
│   ├── test_voice_io.py             (9 tests)
│   │   ├── test_transcribe_audio_success()
│   │   ├── test_transcribe_audio_empty_result()
│   │   ├── test_transcribe_audio_api_error()
│   │   ├── test_speak_response_success()
│   │   ├── test_speak_response_long_text_truncated()
│   │   ├── test_speak_response_empty_text()
│   │   ├── test_speak_response_afplay_not_found()
│   │   ├── test_speak_response_tts_error()
│   │   ├── test_has_mic_available_*()
│   │
│   ├── test_web_fallback.py         (4 tests)
│   │   ├── test_search_web_success()
│   │   ├── test_search_web_api_error()
│   │   ├── test_search_web_result_labeled()
│   │   └── test_search_web_uses_env_model()
│   │
│   └── test_integration.py          (4 tests)
│       ├── test_full_pipeline_found()
│       ├── test_full_pipeline_not_found()
│       ├── test_multiple_formats()
│       └── test_web_fallback_integration()
│
├── 📁 data/                         ⭐ SAMPLE DOCUMENTS
│   └── sample_policy.txt            (Employee handbook - 500+ lines)
│       ├── Section 1: Leave Policy
│       ├── Section 2: Work Arrangement
│       ├── Section 3: Health and Wellness
│       ├── Section 4: Professional Development
│       ├── Section 5: Compensation
│       ├── Section 6: Termination and Severance
│       ├── Section 7: Code of Conduct
│       └── Section 8: Performance and Reviews
│
├── 📁 indexes/                      (Auto-created on first run)
│   └── <file-hash>/
│       ├── index.faiss              (Vector index binary)
│       └── index.pkl                (Metadata)
│
├── 📁 venv/                         (Python virtual environment)
│   ├── bin/
│   │   ├── python
│   │   ├── pip
│   │   └── pytest
│   ├── lib/
│   └── ...
│
├── 📄 README.md                     ⭐ FULL DOCUMENTATION
│   ├── Features overview
│   ├── Setup instructions
│   ├── Usage examples
│   ├── Configuration options
│   ├── Architecture explanation
│   ├── Testing guide
│   ├── Robustness notes
│   ├── Voice tech stack
│   └── Troubleshooting
│
├── 📄 FRONTEND_OPTIONS.md           (Guidance for web/mobile UI)
│   ├── Option 1: Streamlit (MVP/demo)
│   ├── Option 2: FastAPI + React (production)
│   ├── Option 3: Flask/Django (hybrid)
│   ├── Comparison table
│   ├── Deployment suggestions
│   └── Integration guide
│
└── 📄 PROJECT_STRUCTURE.md          (This file)
    └── Complete file tree with descriptions
```

---

## Key Files to Know

### ⭐ Start Here
1. **`.env`** — Add your API key here (just created)
2. **`voice_agent.py`** — Run this to start the agent
3. **`README.md`** — Complete documentation

### 💻 Core Agent (Read in this order)
1. **`app/loaders.py`** — How documents are loaded
2. **`app/chunker.py`** — How documents are split
3. **`app/indexer.py`** — How indexes are built & cached
4. **`app/qa_chain.py`** — How Q&A works (MOST IMPORTANT - strict grounding)
5. **`app/voice_io.py`** — How voice in/out works
6. **`app/web_fallback.py`** — How web search works (optional)

### 🧪 Testing
- **`tests/conftest.py`** — Shared test fixtures
- **`tests/test_*.py`** — 41 tests total, all mocked, all passing

### 📚 Documentation
- **`README.md`** — Setup, usage, architecture
- **`FRONTEND_OPTIONS.md`** — Next steps for web UI
- **`PROJECT_STRUCTURE.md`** — This file

---

## How to Use `.env`

Your `.env` file is now created at:
```
/Users/aneesfatima/genai-projects/voice_doc_agent/.env
```

**Replace this line:**
```
OPENAI_API_KEY=sk-your-key-here
```

**With your actual OpenAI key:**
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The other settings are optional:
- `CHAT_MODEL=gpt-4o-mini` — Change to `gpt-4o` if you want (costs more but faster)
- `TTS_VOICE=alloy` — Try: echo, fable, onyx, nova, shimmer
- `RELEVANCE_THRESHOLD=0.5` — Higher = stricter grounding (less web fallback offers)

---

## Quick Commands

```bash
cd /Users/aneesfatima/genai-projects/voice_doc_agent

# Activate virtual environment
source venv/bin/activate

# Run the agent (text mode first)
python voice_agent.py data/sample_policy.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_qa_chain.py -v

# Run with coverage
pytest --cov=app tests/
```

---

## File Sizes & Line Counts

| File | Lines | Purpose |
|------|-------|---------|
| `app/loaders.py` | 76 | Load PDF/DOCX/TXT |
| `app/chunker.py` | 19 | Chunk documents |
| `app/indexer.py` | 58 | Index building & caching |
| `app/qa_chain.py` | 83 | Grounded Q&A |
| `app/voice_io.py` | 120 | Voice I/O |
| `app/web_fallback.py` | 32 | Web search |
| `voice_agent.py` | 130 | CLI loop |
| **Total Agent Code** | **~518** | Core logic |
| **Test Code** | **~800** | 41 comprehensive tests |
| **Documentation** | **~1000** | README + guides |

---

## What Each Module Does

### 🔄 Document Preparation Pipeline

```
document.pdf
    ↓ (loaders.py)
pages: List[Document]
    ↓ (chunker.py)
chunks: List[Document]
    ↓ (indexer.py)
FAISS vector store
    ↓ (cached to disk by file hash)
indexes/<sha256>/index.faiss
```

### ❓ Query Pipeline

```
user question (voice or text)
    ↓ (voice_io.py if voice)
question text
    ↓ (embedding)
vector
    ↓ (qa_chain.py - similarity search)
top-k chunks + scores
    ↓ (qa_chain.py - threshold check)
    ├─ Below threshold? → "not found" (return early)
    └─ Above threshold? → continue...
        ↓ (qa_chain.py - format prompt)
        ├─ context: top-k chunks
        ├─ question: user query
        └─ instruction: answer ONLY from context
            ↓ (ChatOpenAI)
            answer text
            ↓ (parse for sentinel)
            ├─ found sentinel? → found=False
            └─ no sentinel? → found=True
                ↓ (voice_io.py if voice enabled)
                audio playback
```

---

## Next Steps

1. ✅ **Installed dependencies** — check
2. ✅ **Created `.env` file** — check
3. ⏳ **Add your API key** — YOUR TURN (edit the `.env` file)
4. ⏳ **Run the agent** — Next: `python voice_agent.py data/sample_policy.txt`
5. ⏳ **Try live mic** — After text mode works

---

## Need Help?

- **API key not working?** → Check `.env` file, make sure key starts with `sk-`
- **Module not found?** → Did you `source venv/bin/activate`?
- **Tests failing?** → Run `pytest tests/ -v` to see detailed errors
- **Mic not working?** → Try text mode first, then investigate mic setup
- **Questions about code?** → Check the relevant test file to see how it's used

Good luck! 🚀
