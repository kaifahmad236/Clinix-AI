# ClinixAI — AI Healthcare Assistant (MVP)

A minimal, working full-stack MVP:
- User signup/login (JWT)
- Chat with an AI about general health questions
- Upload a PDF medical report and get an AI-generated summary
- Chat history stored per user
- Dashboard listing previous conversations

## Architecture

**Agents & RAG Pipeline:**
1. **Chat Agent** (`backend/app/agents/chat_agent.py`) — answers health questions, strictly grounded in retrieved medical report excerpts with source citations to prevent hallucinations.
2. **Report Summarizer Agent** (`backend/app/agents/report_agent.py`) — turns raw PDF text into a structured summary (Key Findings / Concerns / Recommendations / Disclaimer).
3. **Orchestrator Agent** (`backend/app/agents/orchestrator.py`) — a **LangGraph** workflow that intelligently routes queries: performs semantic search against the user's private vectorized medical documents, supplying relevant page-level excerpts to the Chat Agent with source attribution.
4. **RAG Vector Store** (`backend/app/rag/vector_store.py`) — powered by **ChromaDB** with user-level tenant isolation. Chunks reports page-by-page, generates embeddings, and retrieves relevant document excerpts.

**Swappable LLM & Embeddings:** `backend/app/llm_config.py` provides `get_llm()` and `get_embeddings()`. To switch providers, edit `.env`:
```
LLM_PROVIDER=gemini   # or: groq
GEMINI_API_KEY=...
GROQ_API_KEY=...
```

## Tech Stack
- Backend: Python + FastAPI
- AI / Orchestration: LangChain + LangGraph
- Vector Store / RAG: ChromaDB (`chromadb` + `langchain-chroma`)
- Frontend: React + Vite + Tailwind CSS
- DB: SQLite (via SQLAlchemy)
- Auth: JWT (python-jose) + bcrypt password hashing

## Project layout
```
clinixai/
  backend/
    app/
      main.py            FastAPI app + router registration
      config.py           env-based settings
      database.py          SQLAlchemy engine/session
      models.py            User, ChatMessage, Report tables
      schemas.py            Pydantic request/response models
      auth.py                JWT + password hashing
      llm_config.py           swappable LLM factory
      agents/
        chat_agent.py
        report_agent.py
        orchestrator.py       LangGraph router (3rd agent)
      rag/
        vector_store.py       ChromaDB indexing, chunking & semantic search
      routers/
        auth_router.py
        chat_router.py
        report_router.py
        dashboard_router.py
    requirements.txt
    .env.example
  frontend/
    src/
      api.js               axios client
      AuthContext.jsx       auth state
      App.jsx                routes
      components/            Navbar, ProtectedRoute
      pages/                  Login, Signup, Chat, Reports, Dashboard
    package.json
    vite.config.js
    tailwind.config.js
```

## Setup

### 1. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set SECRET_KEY to a random string, set LLM_PROVIDER + matching API key
#   Gemini key (free):  https://aistudio.google.com/app/apikey
#   Groq key (free):    https://console.groq.com/keys

uvicorn app.main:app --reload --port 8000
```
Backend runs at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`. SQLite DB file (`clinixai.db`) is created automatically on first run.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173` and talks to the backend at `http://localhost:8000` (see `frontend/src/api.js` — `API_BASE`, change it if you deploy the backend elsewhere).

### 3. Use it
1. Open `http://localhost:5173`, sign up, log in.
2. Go to **Chat** and ask a health question.
3. Go to **Reports**, upload a PDF medical report, get an AI summary.
4. Ask the Chat Agent something like "explain my report" — the Orchestrator will detect that and route the report summary in as context.
5. **Dashboard** lists all your past chat sessions; click one to resume it.

## Notes / MVP limitations (intentional, to keep this shippable)
- PDF summarizer needs a text-based PDF (scanned/image-only PDFs aren't OCR'd in this MVP).
- Chat memory is per-session (grouped by `session_id`), last 10 turns are sent to the LLM to keep context lean.
- No refresh-token flow — JWT expiry is 24h by default (`ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`).
- CORS is locked to `localhost:5173` by default. To allow your deployed frontend, set `FRONTEND_ORIGINS` in `.env` to a comma-separated list of origins (e.g. `https://clinixai.com`). See `backend/app/main.py`.
- Both Gemini and Groq have generous free tiers, but rate limits still apply — if one gets throttled, just flip `LLM_PROVIDER` in `.env`.

## Deployment

### Backend
- Set the required env vars on your host (see `backend/.env.example`): `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DATABASE_URL`, `LLM_PROVIDER`, the matching API key, and `FRONTEND_ORIGINS` (comma-separated production frontend domain(s)).
- The app starts with Uvicorn and honors the `$PORT` env var. Use the provided `Procfile` (e.g. on Render) or run `bash start.sh` directly. Both bind to `0.0.0.0` and use `$PORT` (default `8000`).
- `requirements.txt` lists all dependencies needed to run the backend.

### Frontend
- Build the production bundle with `npm install && npm run build` (outputs to `frontend/dist`).
- The API base URL is read from `VITE_API_URL` at build time. Set it to your deployed backend URL (e.g. `https://api.clinixai.com`) before building; it falls back to `http://localhost:8000` for local dev.
- Serve the static `dist/` folder with any static host (Netlify, Vercel, Nginx, etc.).
