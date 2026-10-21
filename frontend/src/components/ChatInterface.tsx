"use client";

import { useState, useRef, useEffect } from "react";
import ResponseCard from "./ResponseCard";
import LanguageSelector from "./LanguageSelector";
import { sendQuery, QueryResponse } from "@/lib/api";
import GeneralInfoCard from "./GeneralInfoCard";

interface ChatTurn {
  role: "user" | "assistant";
  text: string;
  response?: QueryResponse;
}

const STARTER_PROMPTS = [
  "My employer hasn't paid my salary in two months",
  "I received a defective product and the seller won't refund me",
  "Someone is threatening me online, what can I do?",
];

const LOADING_MESSAGES = [
  "Analyzing your legal question...",
  "Searching applicable laws...",
  "Validating official legal sources...",
  "Preparing your response...",
];

export default function ChatInterface() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [language, setLanguage] = useState("auto");

  const [loading, setLoading] = useState(false);
  const [loadingIndex, setLoadingIndex] = useState(0);

  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [turns, loading]);

  useEffect(() => {
    if (!loading) {
      setLoadingIndex(0);
      return;
    }

    const timer = setInterval(() => {
      setLoadingIndex((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 1500);

    return () => clearInterval(timer);
  }, [loading]);

  const submit = async (text: string) => {
    const trimmed = text.trim();

    if (!trimmed || loading) return;

    setTurns((prev) => [
      ...prev,
      {
        role: "user",
        text: trimmed,
      },
    ]);

    setInput("");
    setLoading(true);
    setError(null);

    try {
      const langParam =
        language === "auto"
          ? null
          : language;

      const res = await sendQuery(
        trimmed,
        sessionId,
        langParam
      );

      setSessionId(res.session_id);

      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          text: res.response_text,
          response: res,
        },
      ]);
    } catch {
      setError(
        "Unable to generate a legal response.\n\nPlease make sure the FastAPI backend is running.\n\nuvicorn backend.main:app --reload"
      );
    } finally {
      setLoading(false);
    }
  };

  console.log("Loading:", loading);

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.wordmark}>
          <span style={styles.wordmarkMain}>
            NyayaMitra
          </span>

          <span style={styles.wordmarkSub}>
            न्यायमित्र
          </span>
        </div>

        <LanguageSelector
          value={language}
          onChange={setLanguage}
        />
      </header>

      <main style={styles.main}>
        {turns.length === 0 && (
          <div style={styles.hero}>
            <h1 style={styles.heroTitle}>
              Understand your legal rights with confidence.
            </h1>

            <p style={styles.heroSub}>
              Ask legal questions in English or your preferred Indian language.
              NyayaMitra explains applicable laws in simple language, cites
              official legal sources, and clearly indicates when additional
              information is needed.
            </p>

            <div style={styles.starters}>
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  style={styles.starterBtn}
                  disabled={loading}
                  onClick={() => submit(prompt)}
                >
                  ⚖️ {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        <div style={styles.thread}>
          {turns.map((turn, index) =>
            turn.role === "user" ? (
              <div
                key={turn.response?.message_id ?? `${turn.role}-${index}`}
                style={styles.userBubbleRow}
              >
                <div style={styles.userBubble}>
                  {turn.text}
                </div>
              </div>
            ) : (
              <div
                key={turn.response?.message_id ?? `${turn.role}-${index}`}
                style={styles.assistantRow}
              >
                {(() => {
  const hasStructuredResponse =
    !!turn.response?.sections?.summary ||
    !!turn.response?.sections?.law ||
    !!turn.response?.sections?.situation ||
    !!turn.response?.sections?.next_steps;

console.log("Response Mode:", turn.response?.response_mode);

  if (turn.response?.awaiting_reply) {
  return (
    <div style={styles.plainBubble}>
      {turn.text}
    </div>
  );
}

if (
  turn.response?.response_mode === "plain" &&
  turn.response
) {
  return (
    <GeneralInfoCard
  content={turn.response.response_text}
  sections={turn.response.sections}
  confidence={turn.response.confidence}
  sessionId={turn.response.session_id}
  messageId={turn.response.message_id}
/>
  );
}

if (hasStructuredResponse && turn.response) {
  return (
    <ResponseCard
      sections={turn.response.sections}
      confidence={turn.response.confidence}
      sessionId={turn.response.session_id}
      messageId={turn.response.message_id}
    />
  );
}

return (
  <div style={styles.plainBubble}>
    {turn.text}
  </div>
);
})()}
              </div>
            )
          )}
                    {loading && (
            <div style={styles.assistantRow}>
              <div style={styles.typingCard}>
                🤖 {LOADING_MESSAGES[loadingIndex]}
              </div>
            </div>
          )}

          {error && (
            <div style={styles.errorBanner}>
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      <footer style={styles.inputBar}>
        <textarea
          spellCheck
          style={styles.input}
          rows={2}
          value={input}
          placeholder="Ask your legal question... (Press Enter to send, Shift+Enter for a new line)"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(input);
            }
          }}
          disabled={loading}
        />

        <button
          style={styles.sendBtn}
          disabled={loading}
          onClick={() => submit(input)}
          >
          ➤
        </button>
      </footer>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 24px",
    borderBottom: "1px solid var(--line)",
    background: "var(--paper-raised)",
  },

  wordmark: {
    display: "flex",
    alignItems: "baseline",
    gap: 8,
  },

  wordmarkMain: {
    fontFamily: "var(--font-display)",
    fontWeight: 700,
    fontSize: 20,
    color: "var(--ink-navy)",
  },

  wordmarkSub: {
    fontSize: 14,
    color: "var(--slate)",
  },

  main: {
    flex: 1,
    overflowY: "auto",
    padding: "28px 24px",
  },

  hero: {
    maxWidth: 620,
    margin: "40px auto",
    textAlign: "center",
  },

  heroTitle: {
    fontFamily: "var(--font-display)",
    fontSize: 30,
    color: "var(--ink-navy)",
    marginBottom: 14,
  },

  heroSub: {
    color: "var(--slate)",
    fontSize: 15,
    lineHeight: 1.7,
    marginBottom: 28,
  },

  starters: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },

  starterBtn: {
    background: "var(--paper-raised)",
    border: "1px solid var(--line)",
    borderRadius: "var(--radius)",
    padding: "12px 16px",
    fontSize: 14,
    textAlign: "left",
    color: "var(--ink-navy-soft)",
    cursor: "pointer",
  },

  thread: {
    display: "flex",
    flexDirection: "column",
    gap: 14,
    maxWidth: 800,
    margin: "0 auto",
  },

  userBubbleRow: {
    display: "flex",
    justifyContent: "flex-end",
  },

  userBubble: {
    background: "var(--ink-navy)",
    color: "var(--paper)",
    borderRadius: "var(--radius)",
    padding: "10px 16px",
    maxWidth: "80%",
    fontSize: 15,
    lineHeight: 1.6,
  },

  assistantRow: {
    display: "flex",
    justifyContent: "flex-start",
  },

  plainBubble: {
    background: "var(--paper-raised)",
    border: "1px solid var(--line)",
    borderRadius: "var(--radius)",
    padding: "12px 16px",
    fontSize: 15,
    lineHeight: 1.7,
    maxWidth: "85%",
  },

  typingCard: {
    background: "var(--paper-raised)",
    border: "1px solid var(--line)",
    borderRadius: "var(--radius)",
    padding: "12px 16px",
    fontStyle: "italic",
    color: "var(--slate)",
    maxWidth: "85%",
  },

  errorBanner: {
    background: "#fbeae5",
    border: "1px solid var(--terracotta)",
    color: "var(--terracotta)",
    borderRadius: "var(--radius)",
    padding: "12px 16px",
    fontSize: 14,
    whiteSpace: "pre-line",
  },

  inputBar: {
    display: "flex",
    gap: 12,
    padding: "18px 24px",
    borderTop: "1px solid var(--line)",
    background: "var(--paper-raised)",
  },

  input: {
    flex: 1,
    fontFamily: "var(--font-ui)",
    fontSize: 15,
    padding: "12px 14px",
    borderRadius: "var(--radius)",
    border: "1px solid var(--line)",
    background: "var(--paper)",
    color: "var(--ink-navy)",
    resize: "none",
    minHeight: 54,
    maxHeight: 140,
    overflowY: "auto",
  },

  sendBtn: {
    background: "var(--seal-gold)",
    color: "var(--ink-navy)",
    border: "none",
    borderRadius: "var(--radius)",
    padding: "12px 24px",
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
  },
};