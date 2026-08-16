import json
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_DIR = os.path.join(os.path.dirname(__file__), "data", "index")

class Retriever:
    def __init__(self, index_dir: str = INDEX_DIR):
        self.index_dir = index_dir
        self._model = None
        self._faiss_index = None
        self._bm25 = None
        self._articles = None
        self._cross_encoder = None

    def _lazy_load(self):
        if self._articles is not None:
            return
        with open(os.path.join(self.index_dir, "articles.json"), encoding="utf-8") as f:
            self._articles = json.load(f)
        self._faiss_index = faiss.read_index(os.path.join(self.index_dir, "faiss.index"))
        with open(os.path.join(self.index_dir, "bm25.pkl"), "rb") as f:
            self._bm25 = pickle.load(f)
        self._model = SentenceTransformer(EMBEDDING_MODEL)
        self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def retrieve_vector(self, query: str, k: int = 5):
        self._lazy_load()
        q_vec = self._model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(q_vec)
        k = min(k, self._faiss_index.ntotal)
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
        k = min(k, len(self._articles))
        top_idxs = np.argsort(scores)[::-1][:k]
        return [(self._articles[i], float(scores[i])) for i in top_idxs]

    def retrieve_hybrid(self, query: str, k: int = 5, vector_weight: float = 0.6):
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

    def rerank(self, query: str, candidates: list, k: int = 5):
        """Re-ranks candidate articles using a CrossEncoder for higher accuracy."""
        if not candidates:
            return []
        self._lazy_load()
        # Pair the query with each document's text
        cross_inp = [[query, c[0]['title'] + " " + c[0]['text']] for c in candidates]
        
        # Predict scores using the CrossEncoder
        scores = self._cross_encoder.predict(cross_inp)
        
        # Zip the scores with the original articles and sort
        reranked = [(candidates[i][0], float(scores[i])) for i in range(len(scores))]
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:k]

