# Frontend Options for Voice Doc Agent

This document compares frontend frameworks for wrapping the voice agent core, enabling multi-user access and a better UX. This is **guidance only** — not implemented in v1.

---

## Option 1: Streamlit (Recommended for MVP/Demo)

**What it is:** Python web framework for rapid data app development. Single-file deployment, hot-reload, built-in component library.

### Pros
- ✅ **Fastest to build** — write UI in Python, minimal web knowledge needed
- ✅ **No separate backend** — Streamlit handles everything; call your agent code directly
- ✅ **Great for prototyping** — launch an MVP in hours, iterate on feedback
- ✅ **Built-in components** — audio player, file uploader, text input, buttons all work out of the box
- ✅ **Easy deployment** — Streamlit Cloud (free tier available)
- ✅ **Multi-session capable** — Streamlit handles session isolation automatically

### Cons
- ❌ **Limited customization** — hard to build deeply custom UI
- ❌ **Performance at scale** — not ideal for 1000+ concurrent users
- ❌ **Mobile experience** — responsive but not native
- ❌ **Architecture constraints** — everything runs in Python; hard to add other services

### When to use
- Building an MVP or demo for stakeholders
- Internal tool for your team (< 100 users)
- You want to iterate fast on features
- You're comfortable with Python

### Getting started
```bash
pip install streamlit
# Create app.py
streamlit run app.py
```

**Example snippet:**
```python
import streamlit as st
from app.loaders import load_document
from app.qa_chain import query_document

st.title("Talk to Your Document")

uploaded_file = st.file_uploader("Upload a document (PDF, DOCX, TXT)")
if uploaded_file:
    # Load and prepare document (cache this!)
    documents = load_document(uploaded_file)
    chunks = chunk_documents(documents)
    vector_store = get_or_build_index(...)
    
    question = st.text_input("Ask a question:")
    if question:
        answer, found, sources = query_document(vector_store, question)
        st.write(f"**Answer:** {answer}")
        
        # Audio playback (Streamlit-native)
        if st.checkbox("Play audio response"):
            speak_response(answer)  # Your existing TTS function
```

---

## Option 2: React + FastAPI (Recommended for Production)

**What it is:** FastAPI (Python backend API) + React (TypeScript frontend).  
Decoupled architecture, scalable, professional-grade UX.

### Pros
- ✅ **Fully decoupled** — frontend and backend can scale independently
- ✅ **Rich UI capabilities** — React ecosystem is massive
- ✅ **Mobile-friendly** — React Native for iOS/Android later
- ✅ **Production-ready** — battle-tested for high traffic
- ✅ **Better performance** — frontend is static assets; backend is optimized API
- ✅ **Team-friendly** — frontend devs don't need Python; backend devs don't touch React

### Cons
- ❌ **Slower to build** — need frontend + backend + API design; more setup
- ❌ **Infrastructure overhead** — need separate deployments, monitoring, DB
- ❌ **More complex** — debugging involves multiple layers
- ❌ **Cost at scale** — multiple servers, more infrastructure needed

### When to use
- Building a SaaS product (100+ users)
- You need a mobile app too
- Team has dedicated frontend and backend devs
- You're planning to add other services (payment, analytics, etc.)

### Architecture
```
User Browser
     │
     ├─ React SPA (TypeScript)
     │  ├─ Document upload
     │  ├─ Voice recorder
     │  ├─ Text input
     │  └─ Audio player
     │
     ▼ (REST/WebSocket)
FastAPI Backend
     │
     ├─ /upload  — receive document → prepare index
     ├─ /query   — question → answer (SSE for streaming)
     ├─ /audio   — text → audio bytes (TTS)
     └─ /transcribe — audio bytes → text (STT)
     │
     ▼
[Your existing agent code]
     ├─ loaders.py
     ├─ chunker.py
     ├─ indexer.py
     ├─ qa_chain.py
     ├─ voice_io.py
     └─ web_fallback.py
```

### Getting started
```bash
# Backend
pip install fastapi uvicorn python-multipart
# Create backend/main.py

# Frontend
npx create-react-app frontend --template typescript
# Create React components in frontend/src/
```

**Example FastAPI endpoint:**
```python
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from app.qa_chain import query_document

app = FastAPI()

@app.post("/query")
async def query(question: str, doc_id: str):
    # Load cached index for doc_id
    vector_store = load_vector_store(f"indexes/{doc_id}")
    answer, found, sources = query_document(vector_store, question)
    
    return {
        "answer": answer,
        "found": found,
        "sources": sources
    }

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    text = transcribe_audio(audio_bytes)
    return {"text": text}
```

---

## Option 3: Hybrid (Flask/Django + HTML/CSS/JS)

**What it is:** Traditional backend (Flask or Django) + server-rendered or AJAX frontend.  
Middle ground between Streamlit and React.

### Pros
- ✅ **Simpler than React** — less JavaScript, easier to understand
- ✅ **Backend-centric** — Python developers can build it solo
- ✅ **Deployable** — many hosting options (Heroku, PythonAnywhere, etc.)

### Cons
- ❌ **Less modern** — no SPA-level interactivity
- ❌ **Page refreshes** — slower UX than React
- ❌ **Not ideal for mobile** — responsive but not native
- ❌ **JavaScript needed** — still need to write some JS for interactivity

### When to use
- Simple internal tool (internal team)
- You want something between Streamlit and React
- You're familiar with Flask or Django

---

## Quick Comparison Table

| Feature | Streamlit | FastAPI+React | Flask/Django |
|---------|-----------|---------------|--------------|
| **Time to MVP** | 1-2 days | 1-2 weeks | 3-5 days |
| **Scalability** | < 100 users | 10,000+ users | 100-1000 users |
| **Mobile Support** | Web only | Web + Native (RN) | Web only |
| **Customization** | Low | Very High | Medium |
| **Learning Curve** | Very Easy | Medium | Easy |
| **Production Ready** | For SMBs | For Enterprise | For SMBs |
| **Cost at Scale** | Low | Medium | Low-Medium |
| **Team Fit** | Solo/Small | Medium/Large | Solo/Small |

---

## Deployment Suggestions

### Streamlit
- **Free:** Streamlit Cloud (built-in, just push to GitHub)
- **Paid:** AWS/GCP/Azure with Docker container

### FastAPI + React
- **Backend:** Render, Railway, Fly.io, AWS Lambda
- **Frontend:** Vercel, Netlify (static hosting)
- **Database (if needed):** PostgreSQL on managed service (e.g., AWS RDS)

### Flask/Django
- **Traditional:** Heroku (deprecated but easier), PythonAnywhere, AWS Elastic Beanstalk
- **Modern:** Docker on Render, Railway, Fly.io

---

## Recommendation for YOUR Project

**For immediate next steps (v2):**
→ **Start with Streamlit** if:
- You want to demo this to users/stakeholders quickly
- Your team is Python-only
- You expect < 200 concurrent users

→ **Go with FastAPI + React** if:
- You're building a product to sell or share widely
- You want to add mobile support later
- You have (or will hire) frontend developers

---

## How to Integrate Your Agent

Whichever frontend you choose, your existing agent code stays the same:

```python
# These don't change regardless of frontend
from app.loaders import load_document
from app.chunker import chunk_documents
from app.indexer import get_or_build_index
from app.qa_chain import query_document
from app.voice_io import transcribe_audio, speak_response
from app.web_fallback import search_web_for_answer

# Just wrap it with a web interface (Streamlit, FastAPI, or Flask)
```

The agent's modular design means the frontend layer is completely independent. You can:
- Swap frontends later without touching the agent code
- Test the agent standalone (pytest suite)
- Reuse the agent in multiple frontends
- Deploy agent and frontend separately

---

## Recommended Next Steps

1. **Get this CLI agent working end-to-end** (with real mic + your OpenAI key)
   - Run the sample tests ✅
   - Test with `sample_policy.txt` in text mode
   - Try live mic recording once

2. **Choose a frontend** based on timeline and team
   - Quick demo? → Streamlit
   - Long-term product? → FastAPI + React

3. **Wrap the agent** with your chosen frontend
   - Streamlit: straightforward, call functions directly
   - FastAPI: design REST endpoints, host separately
   - Flask: traditional web app structure

4. **Add multi-user handling**
   - Streamlit handles session isolation automatically
   - FastAPI: add user auth (JWT, OAuth2) + per-user index cache
   - Flask: similar to FastAPI but more boilerplate

5. **Scale indexing**
   - Current: single file → one FAISS index
   - v2: multiple documents per user → separate indexes or consolidated vector DB (Pinecone, Weaviate)

---

## Questions?

- Need clarification on any option? → Review the architecture diagram and README
- Ready to implement? → Pick a frontend, start building
- Performance concerns? → Start with Streamlit MVP, profile, scale if needed
