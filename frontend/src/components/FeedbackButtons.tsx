"use client";

import { useState } from "react";
import { sendFeedback } from "@/lib/api";

interface FeedbackButtonsProps {
  queryId: string;
}

export function FeedbackButtons({ queryId }: FeedbackButtonsProps) {
  const [chosen, setChosen] = useState<1 | -1 | null>(null);
  const [error, setError] = useState(false);

  async function handle(value: 1 | -1) {
    setChosen(value);
    setError(false);
    try {
      await sendFeedback(queryId, value);
    } catch {
      setError(true);
    }
  }

  return (
    <div className="flex items-center gap-3 pt-1">
      <span
        className="font-mono text-[10px] uppercase tracking-[0.14em]"
        style={{ color: "var(--slate-dark)" }}
      >
        Was this accurate?
      </span>
      <button
        onClick={() => handle(1)}
        aria-label="Thumbs up"
        aria-pressed={chosen === 1}
        className="w-7 h-7 rounded-full flex items-center justify-center transition-colors border"
        style={{
          borderColor: chosen === 1 ? "var(--success)" : "var(--slate-dark)",
          color: chosen === 1 ? "var(--success)" : "var(--slate-dark)",
        }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M7 10v12M15 5.88 14 10h6.29a2 2 0 0 1 1.94 2.5l-2.34 9A2 2 0 0 1 18 23H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/>
        </svg>
      </button>
      <button
        onClick={() => handle(-1)}
        aria-label="Thumbs down"
        aria-pressed={chosen === -1}
        className="w-7 h-7 rounded-full flex items-center justify-center transition-colors border"
        style={{
          borderColor: chosen === -1 ? "var(--error)" : "var(--slate-dark)",
          color: chosen === -1 ? "var(--error)" : "var(--slate-dark)",
        }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ transform: "rotate(180deg)" }}>
          <path d="M7 10v12M15 5.88 14 10h6.29a2 2 0 0 1 1.94 2.5l-2.34 9A2 2 0 0 1 18 23H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/>
        </svg>
      </button>
      {chosen && !error && (
        <span className="text-xs" style={{ color: "var(--slate-dark)" }}>
          Thanks — recorded.
        </span>
      )}
      {error && (
        <span className="text-xs" style={{ color: "var(--error)" }}>
          Couldn&apos;t save feedback.
        </span>
      )}
    </div>
  );
}
