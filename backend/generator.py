import os
from groq import Groq

# Removed OLLAMA references as per user request
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are a GDPR compliance assistant. Answer the user's \
question using ONLY the GDPR article text provided below. \
Always cite the article number(s) you used, like "(Article 17)". \
If the provided articles don't contain enough information to answer, say so \
clearly instead of guessing. Keep answers concise and in plain language.
"""

class Generator:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("Set GROQ_API_KEY environment variable")
        self.client = Groq(api_key=self.api_key)

    def build_prompt(self, query: str, retrieved: list) -> str:
        # User Query Rewriting (Bonus point feature) can be added here
        context = "\n\n".join(
            f"--- Article {a['article_number']}: {a['title']} ---\n{a['text']}"
            for a, _ in retrieved
        )
        return f"GDPR ARTICLES:\n{context}\n\nQUESTION: {query}"

    def generate(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        resp = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content

    def rewrite_query(self, query: str) -> str:
        """Bonus feature: Rewrites user query to be more search friendly."""
        rewrite_prompt = f"Rewrite the following question to make it a better search query for finding relevant GDPR articles. Keep it concise.\n\nQuestion: {query}"
        resp = self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": rewrite_prompt}],
            temperature=0.1,
        )
        return resp.choices[0].message.content.strip()
