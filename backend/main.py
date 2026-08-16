"""
FastAPI backend for the GDPR RAG assistant.

Exposes:
    POST /api/query      -> ask a question, get an answer + cited articles
    POST /api/feedback   -> log thumbs up/down on a previous answer
    GET  /api/health      -> basic health check

Run:
    uvicorn main:app --reload --port 8000

CORS is open to localhost:3000 (default Next.js dev port) — tighten this
before deploying publicly.
"""
import os
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))
from rag import GdprRag  # noqa: E402

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "monitoring", "logs.db")

app = FastAPI(title="GDPR RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        os.environ.get("FRONTEND_ORIGIN", ""),
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = GdprRag()


# ---------- DB setup ----------

@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS queries (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                retrieved_articles TEXT NOT NULL,
                retrieval_mode TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                created_at REAL NOT NULL,
                feedback INTEGER
            )
            """
        )
        conn.commit()


init_db()


# ---------- Schemas ----------

class QueryRequest(BaseModel):
    question: str
    k: int = 5
    mode: str = "hybrid"  # "vector" | "bm25" | "hybrid"


class RetrievedArticle(BaseModel):
    article_number: int
    title: str
    score: float


class QueryResponse(BaseModel):
    query_id: str
    question: str
    answer: str
    retrieved_articles: list[RetrievedArticle]
    latency_ms: int


class FeedbackRequest(BaseModel):
    query_id: str
    feedback: int  # 1 = thumbs up, -1 = thumbs down


# ---------- Routes ----------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(400, "question must not be empty")

    start = time.time()
    try:
        result = rag.answer(req.question, k=req.k, mode=req.mode)
    except Exception as e:
        raise HTTPException(500, f"RAG pipeline error: {e}")
    latency_ms = int((time.time() - start) * 1000)

    query_id = str(uuid.uuid4())
    import json as _json

    with get_db() as conn:
        conn.execute(
            "INSERT INTO queries (id, question, answer, retrieved_articles, "
            "retrieval_mode, latency_ms, created_at, feedback) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
            (
                query_id,
                req.question,
                result["answer"],
                _json.dumps(result["retrieved_articles"]),
                req.mode,
                latency_ms,
                time.time(),
            ),
        )
        conn.commit()

    return QueryResponse(
        query_id=query_id,
        question=req.question,
        answer=result["answer"],
        retrieved_articles=result["retrieved_articles"],
        latency_ms=latency_ms,
    )


@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    if req.feedback not in (1, -1):
        raise HTTPException(400, "feedback must be 1 or -1")
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE queries SET feedback = ? WHERE id = ?",
            (req.feedback, req.query_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "query_id not found")
    return {"status": "ok"}
