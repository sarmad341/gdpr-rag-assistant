"""
Retrieval Evaluation Script

This script evaluates the performance of different retrieval methods (vector vs. hybrid).
It measures Hit Rate and Mean Reciprocal Rank (MRR) across a predefined set of evaluation questions.
"""
import os
import sys

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(__file__))
from retriever import Retriever

# Sample Evaluation Dataset: (Query, Expected Article Number)
EVAL_DATASET = [
    ("What are the conditions for consent?", 7),
    ("When is a data protection officer required?", 37),
    ("What is the right to be forgotten?", 17),
    ("How long do we have to report a data breach?", 33),
    ("Can we process data about racial or ethnic origin?", 9),
    ("What information must be provided when collecting data from the subject?", 13),
    ("What are the penalties for violating the GDPR?", 83),
    ("What rights does a user have regarding automated decision making?", 22),
    ("Do I need to keep records of processing activities?", 30),
    ("Under what conditions can data be transferred to a third country?", 46),
]

def calculate_metrics(retriever: Retriever, mode: str, k: int = 5):
    hits = 0
    mrr_sum = 0.0

    for query, expected_article in EVAL_DATASET:
        # Retrieve top k articles
        results = retriever.retrieve(query, k=k, mode=mode)
        
        # Check if expected article is in results
        retrieved_articles = [res[0]['article_number'] for res in results]
        
        if expected_article in retrieved_articles:
            hits += 1
            rank = retrieved_articles.index(expected_article) + 1
            mrr_sum += 1.0 / rank

    total = len(EVAL_DATASET)
    hit_rate = hits / total
    mrr = mrr_sum / total
    
    return hit_rate, mrr

if __name__ == "__main__":
    print("Loading indices...")
    retriever = Retriever()
    
    print("\n--- Evaluating Vector Search Only ---")
    vec_hr, vec_mrr = calculate_metrics(retriever, mode="vector")
    print(f"Hit Rate: {vec_hr:.2f} | MRR: {vec_mrr:.2f}")

    print("\n--- Evaluating Hybrid Search (Vector + BM25) ---")
    hyb_hr, hyb_mrr = calculate_metrics(retriever, mode="hybrid")
    print(f"Hit Rate: {hyb_hr:.2f} | MRR: {hyb_mrr:.2f}")

    print("\nConclusion: Hybrid Search usually outperforms Vector-only search because it catches exact keyword matches (like specific article names) alongside semantic meaning.")
