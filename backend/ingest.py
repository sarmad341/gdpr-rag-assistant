"""
Ingestion pipeline: loads gdpr_articles.json, generates embeddings,
builds a FAISS vector index and a BM25 keyword index, and saves everything
to disk for the RAG app to load at query time.

Automated via Prefect for workflow orchestration.

Usage:
    python ingest.py
"""
import argparse
import json
import os
import pickle

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from prefect import flow, task

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

@task(name="Load Articles")
def load_articles(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_corpus_text(article: dict) -> str:
    return f"Article {article['article_number']} - {article['title']}\n{article['text']}"

def tokenize(text: str):
    return text.lower().split()

@task(name="Generate Embeddings")
def generate_embeddings(corpus_texts: list[str]):
    print(f"Loading embedding model ({EMBEDDING_MODEL})...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Generating embeddings...")
    embeddings = model.encode(
        corpus_texts, show_progress_bar=True, convert_to_numpy=True
    )
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)
    return embeddings

@task(name="Build FAISS Index")
def build_faiss_index(embeddings, out_dir: str):
    print("Building FAISS index...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, os.path.join(out_dir, "faiss.index"))

@task(name="Build BM25 Index")
def build_bm25_index(corpus_texts: list[str], out_dir: str):
    print("Building BM25 index...")
    tokenized_corpus = [tokenize(t) for t in corpus_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(os.path.join(out_dir, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)

@task(name="Save Metadata")
def save_metadata(articles: list[dict], out_dir: str):
    with open(os.path.join(out_dir, "articles.json"), "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

@flow(name="GDPR Ingestion Flow")
def ingestion_flow(data_path: str = "data/gdpr_articles.json", out_dir: str = "data/index"):
    # Fix paths to be relative to the script directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path_full = os.path.join(base_dir, data_path)
    out_dir_full = os.path.join(base_dir, out_dir)
    
    os.makedirs(out_dir_full, exist_ok=True)
    
    articles = load_articles(data_path_full)
    corpus_texts = [build_corpus_text(a) for a in articles]
    
    embeddings = generate_embeddings(corpus_texts)
    
    build_faiss_index(embeddings, out_dir_full)
    build_bm25_index(corpus_texts, out_dir_full)
    save_metadata(articles, out_dir_full)
    
    print(f"Done. Index artifacts written to {out_dir_full}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/gdpr_articles.json")
    parser.add_argument("--out", default="data/index")
    args = parser.parse_args()
    
    ingestion_flow(data_path=args.data, out_dir=args.out)
