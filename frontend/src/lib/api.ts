export interface RetrievedArticle {
  article_number: number;
  title: string;
  score: number;
}

export interface QueryResponse {
  query_id: string;
  question: string;
  answer: string;
  retrieved_articles: RetrievedArticle[];
  latency_ms: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function askQuestion(
  question: string,
  mode: "vector" | "bm25" | "hybrid" = "hybrid"
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, mode }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export async function sendFeedback(
  queryId: string,
  feedback: 1 | -1
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query_id: queryId, feedback }),
  });
  if (!res.ok) {
    throw new Error(`Feedback request failed (${res.status})`);
  }
}
