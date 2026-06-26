# HCAI-ITS — Intelligent Tutoring System for Python

A full-stack, production-ready Intelligent Tutoring System (ITS) for Python basics, powered by **Groq LLM** (llama-3.3-70b-versatile), **Supabase pgvector RAG**, and **SentenceTransformers** (all-MiniLM-L6-v2, 384-dim).

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 React Frontend                  │
│  ChatPage │ QuizPage │ Dashboard │ PDFUploader  │
└──────────────────────┬──────────────────────────┘
                       │ Axios / REST
┌──────────────────────▼──────────────────────────┐
│              FastAPI Backend (Python)           │
│  auth │ ask │ assessments │ mastery │ admin     │
│                                                 │
│  RAG Pipeline:                                  │
│  PDFLoader → Chunker → Embeddings → pgvector    │
│                                                 │
│  Tutor Engine:                                  │
│  Question → Retrieve chunks → Build prompt      │
│          → Groq LLM → Persist → Respond         │
└──────────────┬──────────────────────────────────┘
               │ supabase-py
┌──────────────▼──────────────────────────────────┐
│              Supabase (PostgreSQL + pgvector)   │
│  textbook_chunks │ student_mastery │ assessments│
│  assessment_questions │ learning_events │ messages│
└─────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn, Python 3.11 |
| LLM | Groq API (llama-3.3-70b-versatile) |
| Embeddings | SentenceTransformers all-MiniLM-L6-v2 (384-dim) |
| Database | Supabase (PostgreSQL + pgvector) |
| Frontend | React 18 + Vite, Vanilla CSS |
| Auth | JWT (HS256) + OTP email |
| PDF parsing | PyPDF2 |
| Containerization | Docker + Docker Compose |

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- A **Supabase** project ([create one free](https://supabase.com))
- A **Groq API key** ([get one free](https://console.groq.com/keys))

---

## Setup Instructions

### 1. Clone and navigate

```bash
git clone <your-repo-url>
cd HCAI-ITS
```

### 2. Configure environment variables

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and fill in:
- `SUPABASE_URL` and `SUPABASE_KEY` from your Supabase project settings
- `GROQ_API_KEY` from console.groq.com/keys  ← **Required for LLM responses**
- `SECRET_KEY` — any random 32+ char string

### 3. Set up the Supabase database

In your Supabase dashboard → **SQL Editor** → **New Query**, paste and run:

```
supabase/migrations/001_initial_schema.sql
```

This creates all 6 tables and the `match_chunks` RPC for pgvector similarity search.

### 4. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Note:** First run downloads the SentenceTransformer model (~90 MB). This is cached automatically.

### 5. Seed sample assessments

```bash
cd backend
python seed_data.py
```

This inserts 3 assessments (Variables, Functions, Loops) with 3 MCQs each. Safe to run multiple times (idempotent).

### 6. Ingest the corpus (optional — or use PDF upload)

```bash
cd backend
python -m app.rag.ingest
```

Or use the **PDF Uploader** on the Dashboard to ingest any Python textbook.

### 7. Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API available at: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`

### 8. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## Running with Docker

```bash
# Build and start both services
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ask` | Ask the AI tutor a question (RAG + Groq) |
| GET | `/api/tutor/history/{student_id}` | Recent chat messages |
| GET | `/assessments/{concept}` | Get quiz for a concept |
| POST | `/assessments/submit` | Submit quiz answers |
| GET | `/mastery/` | All mastery scores |
| GET | `/mastery/weak` | Concepts with score < 0.5 |
| GET | `/mastery/strong` | Concepts with score > 0.7 |
| POST | `/api/admin/ingest-pdf` | Upload PDF to knowledge base |
| GET | `/api/admin/chunks` | Inspect stored chunks |
| POST | `/auth/register` | Register new student |
| POST | `/auth/login` | Login (returns JWT) |
| POST | `/demo/login` | Login as demo persona |
| GET | `/health` | Health check |

---

## Key Implementation Details

### RAG Pipeline

1. **PDF Upload** → `PDFUploader.jsx` → `POST /api/admin/ingest-pdf`
2. **Text Extraction** → `pdf_loader.py` (PyPDF2) — one tuple per page
3. **Chunking** → `chunker.py` — ~500 chars, 50 char overlap, sentence-aware
4. **Embedding** → `embeddings.py` — all-MiniLM-L6-v2, 384-dim, normalized
5. **Storage** → `vector_store.py` — Supabase `textbook_chunks` table
6. **Retrieval** → `retrieval.py` — top-5 by cosine similarity via `match_chunks` RPC

### Tutoring Engine

- Adaptive prompt based on mastery score:
  - `< 0.4`: simple language + analogies + quiz suggestion
  - `0.4–0.7`: moderate detail with examples
  - `> 0.7`: advanced, concise, Pythonic
- Uses top-3 retrieved chunks + last 5 messages as context
- Falls back to intelligent template stub if GROQ_API_KEY is not set

### Mastery Update Formula

```
new_mastery = (old_mastery × 0.7) + (quiz_score × 0.3)
```

Bounded to `[0.0, 1.0]`. Applied after every quiz submission.

---

## Demo Personas

Run `python backend/seed_personas.py` to create 3 demo users:

| Persona | Username | Mastery Level |
|---|---|---|
| Ava 🌱 | ava_beginner | Low (beginner) |
| Marcus 📚 | marcus_inter | Medium (intermediate) |
| Priya 🔥 | priya_advanced | High (advanced) |

Password for all: `DemoPass123!`

Access via the persona selector on the login screen.

---

## Project Structure

```
HCAI-ITS/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app + router registration
│   │   ├── api/                     # REST endpoint routers
│   │   │   ├── admin.py             # PDF ingest + chunk inspection
│   │   │   ├── ask.py               # POST /api/ask + GET /api/tutor/history
│   │   │   ├── assessments.py       # Quiz fetch + submit
│   │   │   ├── mastery.py           # Mastery + /weak + /strong
│   │   │   └── ...
│   │   ├── application/
│   │   │   └── tutor_service.py     # Groq LLM orchestration
│   │   ├── rag/
│   │   │   ├── pdf_loader.py        # PyPDF2 text extraction
│   │   │   ├── chunker.py           # Text chunking
│   │   │   ├── embeddings.py        # SentenceTransformer
│   │   │   ├── vector_store.py      # Supabase upsert
│   │   │   └── retrieval.py         # pgvector similarity search
│   │   └── infrastructure/
│   │       ├── mastery_repository.py
│   │       ├── chat_repository.py
│   │       └── ...
│   ├── seed_data.py                 # Seed 3 sample assessments
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── frontend/
│   └── src/
│       ├── pages/                   # ChatPage, QuizPage, DashboardPage
│       ├── components/
│       │   ├── PDFUploader.jsx      # Drag-and-drop PDF ingestion
│       │   └── ...
│       └── hooks/useMastery.js
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql   # Complete DB schema + pgvector RPC
└── docker-compose.yml
```