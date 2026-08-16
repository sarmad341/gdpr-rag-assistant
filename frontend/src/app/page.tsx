"use client";

import { useState } from "react";
import { askQuestion, type QueryResponse } from "@/lib/api";
import { ArticleStamp } from "@/components/ArticleStamp";
import { FeedbackButtons } from "@/components/FeedbackButtons";

const EXAMPLE_QUESTIONS = [
  "What is the right to be forgotten?",
  "Do I need a Data Protection Officer?",
  "How long do I have to report a data breach?",
  "Can I store user data outside the EU?",
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(q?: string) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await askQuestion(text);
      setResult(res);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Something went wrong reaching the API."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main
      className="flex-1 flex flex-col items-center px-6 py-16 md:py-24"
      style={{ background: "var(--ink)" }}
    >
      <div className="w-full max-w-2xl flex flex-col gap-10">
        {/* Header */}
        <header className="flex flex-col gap-3 text-center">
          <span
            className="font-mono text-[11px] uppercase tracking-[0.2em] mx-auto"
            style={{ color: "var(--brass)" }}
          >
            Regulation (EU) 2016/679
          </span>
          <h1
            className="font-serif text-4xl md:text-5xl font-semibold tracking-tight"
            style={{ color: "#f2efe6" }}
          >
            Ask the GDPR
          </h1>
          <p className="text-sm md:text-base leading-relaxed max-w-md mx-auto" style={{ color: "var(--slate)" }}>
            Plain-English questions, answered and cited directly from the
            actual regulation — not a guess.
          </p>
        </header>

        {/* Query form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="flex flex-col gap-3"
        >
          <div
            className="flex items-center gap-2 rounded-xl border px-4 py-3 transition-colors focus-within:border-[var(--brass)]"
            style={{ borderColor: "var(--ink-light)", background: "var(--ink-light)" }}
          >
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Can I keep customer data after they cancel their account?"
              className="flex-1 bg-transparent outline-none text-sm md:text-base placeholder:opacity-50"
              style={{ color: "#f2efe6" }}
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="shrink-0 rounded-lg px-4 py-2 text-sm font-medium transition-opacity disabled:opacity-40"
              style={{ background: "var(--brass)", color: "var(--ink)" }}
            >
              {loading ? "Searching…" : "Ask"}
            </button>
          </div>

          {/* Example questions */}
          {!result && !loading && (
            <div className="flex flex-wrap gap-2 justify-center pt-2">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => {
                    setQuestion(q);
                    handleSubmit(q);
                  }}
                  className="text-xs rounded-full border px-3 py-1.5 transition-colors hover:border-[var(--brass)]"
                  style={{ borderColor: "var(--ink-light)", color: "var(--slate)" }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}
        </form>

        {/* Loading state */}
        {loading && (
          <div className="flex flex-col items-center gap-3 py-10">
            <div
              className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
              style={{ borderColor: "var(--brass)", borderTopColor: "transparent" }}
            />
            <span className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--slate-dark)" }}>
              Searching the regulation
            </span>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div
            className="rounded-lg border px-4 py-3 text-sm"
            style={{ borderColor: "var(--error)", color: "var(--error)" }}
          >
            {error}. Is the API running at{" "}
            <code className="font-mono">localhost:8000</code>?
          </div>
        )}

        {/* Result */}
        {result && !loading && (
          <div className="flex flex-col gap-6">
            {/* Answer, in parchment — reads like the actual page of law */}
            <div
              className="rounded-2xl p-6 md:p-8 border"
              style={{
                background: "var(--parchment)",
                borderColor: "var(--parchment-line)",
              }}
            >
              <p
                className="font-mono text-[10px] uppercase tracking-[0.16em] mb-3"
                style={{ color: "var(--brass)" }}
              >
                Answer
              </p>
              <p
                className="font-serif text-lg leading-relaxed whitespace-pre-wrap"
                style={{ color: "var(--ink)" }}
              >
                {result.answer}
              </p>
            </div>

            {/* Cited articles */}
            {result.retrieved_articles.length > 0 && (
              <div className="flex flex-col gap-4">
                <p
                  className="font-mono text-[10px] uppercase tracking-[0.16em]"
                  style={{ color: "var(--slate-dark)" }}
                >
                  Grounded in
                </p>
                <div className="flex flex-col gap-4">
                  {result.retrieved_articles.map((a) => (
                    <ArticleStamp
                      key={a.article_number}
                      articleNumber={a.article_number}
                      title={a.title}
                    />
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <FeedbackButtons queryId={result.query_id} />
              <span
                className="font-mono text-[10px]"
                style={{ color: "var(--slate-dark)" }}
              >
                {result.latency_ms}ms
              </span>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
