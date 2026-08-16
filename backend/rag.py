"""
Core RAG flow: retrieve relevant GDPR articles, build a prompt, call the LLM.

Supports two retrieval modes (compare them in Phase 4 eval):
    - "vector"  : semantic search only
    - "hybrid"  : BM25 keyword search + vector search, merged by score

LLM backend is pluggable — set LLM_BACKEND env var to "groq" or "ollama".
Groq: free tier, fast, needs GROQ_API_KEY.
Ollama: fully local, no API key, needs `ollama serve` running with a model
pulled (e.g. `ollama pull llama3.1:8b`).
"""
import json
import os
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "index")

LLM_BACKEND = os.environ.get("LLM_BACKEND", "groq")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

SYSTEM_PROMPT = """You are a GDPR compliance assistant. Answer the user's \
question using ONLY the GDPR article text provided below. \
Always cite the article number(s) you used, like "(Article 17)". \
If the provided articles don't contain enough information to answer, say so \
clearly instead of guessing. Keep answers concise and in plain language.
"""


class GdprRag:
    def __init__(self, index_dir: str = INDEX_DIR):
        self.index_dir = index_dir
        self._model = None
        self._faiss_index = None
        self._bm25 = None
        self._articles = None

    def _lazy_load(self):
        if self._articles is not None:
            return
        with open(os.path.join(self.index_dir, "articles.json"), encoding="utf-8") as f:
            self._articles = json.load(f)
        self._faiss_index = faiss.read_index(os.path.join(self.index_dir, "faiss.index"))
        with open(os.path.join(self.index_dir, "bm25.pkl"), "rb") as f:
            self._bm25 = pickle.load(f)
        self._model = SentenceTransformer(EMBEDDING_MODEL)

    # ---------- Retrieval ----------

    def retrieve_vector(self, query: str, k: int = 5):
        self._lazy_load()
        q_vec = self._model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(q_vec)
        scores, idxs = self._faiss_index.search(q_vec, k)
        return [
            (self._articles[i], float(scores[0][rank]))
            for rank, i in enumerate(idxs[0])
            if i != -1
        ]

    def retrieve_bm25(self, query: str, k: int = 5):
        self._lazy_load()
        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)
        top_idxs = np.argsort(scores)[::-1][:k]
        return [(self._articles[i], float(scores[i])) for i in top_idxs]

    def retrieve_hybrid(self, query: str, k: int = 5, vector_weight: float = 0.6):
        """Merge vector + BM25 rankings via min-max normalized weighted sum.
        This is the retrieval approach compared against vector-only in the
        Phase 4 evaluation — see eval/retrieval_eval.py."""
        self._lazy_load()
        vec_results = self.retrieve_vector(query, k=max(k * 3, 10))
        bm25_results = self.retrieve_bm25(query, k=max(k * 3, 10))

        def normalize(results):
            if not results:
                return {}
            scores = [s for _, s in results]
            lo, hi = min(scores), max(scores)
            span = (hi - lo) or 1.0
            return {
                a["article_number"]: (s - lo) / span for a, s in results
            }

        vec_norm = normalize(vec_results)
        bm25_norm = normalize(bm25_results)
        all_article_nums = set(vec_norm) | set(bm25_norm)

        combined = []
        by_num = {a["article_number"]: a for a, _ in vec_results + bm25_results}
        for num in all_article_nums:
            score = vector_weight * vec_norm.get(num, 0.0) + (1 - vector_weight) * bm25_norm.get(num, 0.0)
            combined.append((by_num[num], score))

        combined.sort(key=lambda x: x[1], reverse=True)
        return combined[:k]

    def retrieve(self, query: str, k: int = 5, mode: str = "hybrid"):
        if mode == "vector":
            return self.retrieve_vector(query, k)
        elif mode == "bm25":
            return self.retrieve_bm25(query, k)
        elif mode == "hybrid":
            return self.retrieve_hybrid(query, k)
        raise ValueError(f"Unknown retrieval mode: {mode}")

    # ---------- Generation ----------

    def build_prompt(self, query: str, retrieved):
        context = "\n\n".join(
            f"--- Article {a['article_number']}: {a['title']} ---\n{a['text']}"
            for a, _ in retrieved
        )
        return f"GDPR ARTICLES:\n{context}\n\nQUESTION: {query}"

    def call_llm(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        if LLM_BACKEND == "groq":
            return self._call_groq(prompt, system_prompt)
        elif LLM_BACKEND == "ollama":
            return self._call_ollama(prompt, system_prompt)
        raise ValueError(f"Unknown LLM_BACKEND: {LLM_BACKEND}")

    def _call_groq(self, prompt: str, system_prompt: str) -> str:
        from groq import Groq  # pip install groq

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Set GROQ_API_KEY environment variable")
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content

    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        import requests  # pip install requests

        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    # ---------- End-to-end ----------

    def answer(self, query: str, k: int = 5, mode: str = "hybrid"):
        retrieved = self.retrieve(query, k=k, mode=mode)
        prompt = self.build_prompt(query, retrieved)
        answer_text = self.call_llm(prompt)
        return {
            "query": query,
            "answer": answer_text,
            "retrieved_articles": [
                {"article_number": a["article_number"], "title": a["title"], "score": s}
                for a, s in retrieved
            ],
        }


if __name__ == "__main__":
    import sys

    rag = GdprRag()
    question = " ".join(sys.argv[1:]) or "What is the right to be forgotten?"
    result = rag.answer(question)
    print("Q:", result["query"])
    print("\nRetrieved articles:")
    for a in result["retrieved_articles"]:
        print(f"  Article {a['article_number']} - {a['title']} (score={a['score']:.3f})")
    print("\nAnswer:\n", result["answer"])
