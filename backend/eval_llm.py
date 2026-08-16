"""
LLM Evaluation Script

This script evaluates different prompt variants to see which produces better, more accurate answers with citations.
"""
import os
import sys

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(__file__))
from generator import Generator
from retriever import Retriever

EVAL_DATASET = [
    "What are the conditions for consent?",
    "When is a data protection officer required?"
]

PROMPT_VARIANT_1 = """You are a GDPR compliance assistant. Answer the user's question using ONLY the GDPR article text provided below. Always cite the article number(s) you used, like "(Article 17)". If the provided articles don't contain enough information to answer, say so clearly instead of guessing. Keep answers concise and in plain language."""

PROMPT_VARIANT_2 = """You are a strict legal analyst. Answer the user's question using ONLY the provided GDPR text. You must begin your answer by explicitly listing the Articles you are referencing. Do not use outside knowledge. If the text does not contain the answer, state 'Insufficient Information'."""

if __name__ == "__main__":
    print("Loading LLM Generator and Retriever...")
    generator = Generator()
    retriever = Retriever()

    for query in EVAL_DATASET:
        print(f"\n=============================================")
        print(f"QUESTION: {query}")
        print(f"=============================================")
        
        # Retrieve context
        retrieved = retriever.retrieve(query, k=3, mode="hybrid")
        prompt = generator.build_prompt(query, retrieved)

        print("\n--- VARIANT 1 (Plain Language + Inline Citation) ---")
        answer_1 = generator.generate(prompt, system_prompt=PROMPT_VARIANT_1)
        print(answer_1)

        print("\n--- VARIANT 2 (Strict Analyst + Prefix Citation) ---")
        answer_2 = generator.generate(prompt, system_prompt=PROMPT_VARIANT_2)
        print(answer_2)
