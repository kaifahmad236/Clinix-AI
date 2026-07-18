# ClinixAI — AI Healthcare Assistant (MVP)

A minimal, working full-stack MVP:
- User signup/login (JWT)
- Chat with an AI about general health questions
- Upload a PDF medical report and get an AI-generated summary
- Chat history stored per user
- Dashboard listing previous conversations

## Architecture

**3 Agents:**
1. **Chat Agent** (`backend/app/agents/chat_agent.py`) — answers health questions, aware of prior turns and (optionally) the user's latest report summary.
2. **Report Summarizer Agent** (`backend/app/agents/report_agent.py`) — turns raw PDF text into a structured summary (Key Findings / Concerns / Recommendations / Disclaimer).
3. **Orchestrator Agent** (`backend/app/agents/orchestrator.py`) — a small **LangGraph** graph that routes each chat message: if it looks like the user is asking about their uploaded report, it hands the Chat Agent that report's summary as context; otherwise it's a plain health chat. This is the router the spec's "3 agents" implied but didn't name — swap/extend its routing logic in one file if you want smarter behavior later.

**Swappable LLM:** `backend/app/llm_config.py` has one `get_llm()` function used by both agents. To switch providers, edit `.env`:
```
LLM_PROVIDER=gemini   # or: groq
GEMINI_API_KEY=...
GROQ_API_KEY=...
```
No code changes needed — both free-tier providers (Google AI Studio, Groq) are wired up already.

## Tech Stack
- Backend: Python + FastAPI
- AI: LangChain + LangGraph
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
- CORS is currently locked to `localhost:5173`; update `app/main.py` if you deploy the frontend elsewhere.
- Both Gemini and Groq have generous free tiers, but rate limits still apply — if one gets throttled, just flip `LLM_PROVIDER` in `.env`.
