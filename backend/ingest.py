"""
Ingestion pipeline: loads gdpr_articles.json, generates embeddings,
builds a FAISS vector index and a BM25 keyword index, and saves everything
to disk for the RAG app to load at query time.

Usage:
    python ingest.py --data ../data/gdpr_articles.json --out ../data/index

Uses sentence-transformers (all-MiniLM-L6-v2) — runs on CPU, no API key
needed, ~80MB download on first run.
"""
import argparse
import json
import os
import pickle

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_articles(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_corpus_text(article: dict) -> str:
    """Text used for embedding + BM25: title + body, so semantic search
    catches queries that match the article's subject even if the exact
    wording differs."""
    return f"Article {article['article_number']} - {article['title']}\n{article['text']}"


def tokenize(text: str):
    return text.lower().split()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="../data/gdpr_articles.json")
    parser.add_argument("--out", default="../data/index")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print("Loading articles...")
    articles = load_articles(args.data)
    print(f"  {len(articles)} articles loaded")

    corpus_texts = [build_corpus_text(a) for a in articles]

    print(f"Loading embedding model ({EMBEDDING_MODEL})...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Generating embeddings...")
    embeddings = model.encode(
        corpus_texts, show_progress_bar=True, convert_to_numpy=True
    )
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)  # so inner product == cosine similarity

    print("Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # exact search, fine at this corpus size
    index.add(embeddings)
    faiss.write_index(index, os.path.join(args.out, "faiss.index"))

    print("Building BM25 index...")
    tokenized_corpus = [tokenize(t) for t in corpus_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(os.path.join(args.out, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)

    # Save the article metadata in the SAME order as the index vectors,
    # so an index position can be mapped back to its article.
    with open(os.path.join(args.out, "articles.json"), "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print(f"Done. Index artifacts written to {args.out}/")
    print("  - faiss.index   (vector search)")
    print("  - bm25.pkl      (keyword search)")
    print("  - articles.json (metadata, same order as index)")


if __name__ == "__main__":
    main()
