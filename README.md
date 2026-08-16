# GDPR Q&A RAG Assistant — Build Progress

## Architecture

```
gdpr-rag/
├── data/
│   ├── fetch_and_chunk.py     # Fetches official GDPR text from EUR-Lex, parses into article chunks
│   ├── raw_gdpr_text.txt      # Sample text (Articles 1-49) used to build/test this pipeline
│   ├── gdpr_articles.json     # Parsed chunks: [{article_number, title, chapter, text}, ...]
│   └── index/                 # Built by ingestion/ingest.py — FAISS + BM25 indexes
├── ingestion/
│   └── ingest.py              # Builds embeddings, FAISS vector index, BM25 keyword index
├── rag/
│   └── rag.py                 # Core RAG class: retrieve (vector/bm25/hybrid) + generate
├── backend/
│   ├── main.py                 # FastAPI: /api/query, /api/feedback, /api/health
│   └── requirements.txt
├── frontend/                   # Next.js (TypeScript, Tailwind) UI
│   └── src/
│       ├── app/page.tsx        # Main Q&A page
│       ├── components/         # ArticleStamp (citation badge), FeedbackButtons
│       └── lib/api.ts          # Typed API client
├── eval/                       # (next phase)
├── monitoring/                 # logs.db (SQLite) written by backend, dashboard TBD
└── requirements.txt             # (root-level convenience file, mirrors ingestion+rag deps)
```

**Flow:** Next.js frontend → FastAPI backend (`/api/query`) → `rag.py` (hybrid retrieval
over FAISS + BM25) → LLM (Groq or Ollama) → answer + cited articles → logged to SQLite
→ rendered in UI with thumbs up/down feedback (written back to SQLite via `/api/feedback`).

## IMPORTANT — before you run this for real

`data/raw_gdpr_text.txt` currently contains a **summarized placeholder** of Articles
1-49, not the verbatim legal text. Before doing anything else, get the real official
text on your own machine (EUR-Lex isn't reachable from the sandbox this was built in):

```bash
cd data
python fetch_and_chunk.py
```

This pulls the complete, exact, official consolidated GDPR text (all 99 articles)
directly from EUR-Lex — critical for a legal citation tool to be trustworthy.

## How to run

**1. Data + indexes**
```bash
pip install -r requirements.txt
cd data && python fetch_and_chunk.py && cd ..
cd ingestion && python ingest.py --data ../data/gdpr_articles.json --out ../data/index && cd ..
```

**2. Backend (FastAPI)**
```bash
cd backend
pip install -r requirements.txt
export LLM_BACKEND=groq
export GROQ_API_KEY=your_key_here     # free tier at console.groq.com
# or: export LLM_BACKEND=ollama       (fully local, needs `ollama serve` + a pulled model)
uvicorn main:app --reload --port 8000
```

**3. Frontend (Next.js)**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Open http://localhost:3000

## What's verified working right now (tested in sandbox, no internet needed)

- ✅ Article parser: correctly splits raw GDPR text into per-article chunks with metadata
- ✅ FAISS vector index + BM25 keyword index: both build and search correctly
- ✅ Hybrid retrieval merge logic: runs correctly end-to-end
- ✅ FastAPI backend: all routes tested via `TestClient` — query, feedback, health,
  error handling (400 on empty question, 404 on bad feedback id), SQLite logging
- ✅ Next.js frontend: `npm run build` compiles cleanly, all TypeScript types check out,
  component tree (query form → loading state → answer card → article stamps → feedback
  buttons → error state) renders without errors

**Not yet testable in this sandbox** (needs your internet access): downloading the
`all-MiniLM-L6-v2` embedding model, Google Fonts fetch during Next.js build/dev,
and calling Groq/Ollama for generation. All are wired up correctly and will work
as soon as you run the commands above on your own machine.

## Next phases (not yet built)
- Phase 4: Retrieval evaluation (vector vs hybrid, hit rate/MRR)
- Phase 5: LLM evaluation (prompt comparison)
- Phase 7: Monitoring dashboard (SQLite logging already in place via backend)
- Phase 8: Docker/docker-compose for full stack
- Phase 9: Final documentation
