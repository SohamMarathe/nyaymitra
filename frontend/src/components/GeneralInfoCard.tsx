"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import ConfidenceMeter from "./ConfidenceMeter";
import {
  ResponseSections,
  sendFeedback,
} from "@/lib/api";

interface Props {
  content: string;
  sections: ResponseSections;
  confidence: "high" | "medium" | "low" | null;
  sessionId: string | null;
  messageId: string;
}

export default function GeneralInfoCard({
  content,
  sections,
  confidence,
  sessionId,
  messageId,
}: Props) {
  const [copied, setCopied] = useState(false);
  const [sourcesOpen, setSourcesOpen] =
    useState(false);

  const [feedbackGiven, setFeedbackGiven] =
    useState<"up" | "down" | null>(null);

  const article = content
  .replace(/\n📚\s*SOURCES[\s\S]*$/i, "")
  .replace(/\n_Confidence:[\s\S]*$/i, "")
  .replace(/\n---[\s\S]*$/i, "")
  .trim();

  async function handleCopy() {
    const text = [
      article,

      sections.sources
        ? `\n\nSources\n${sections.sources}`
        : "",

      sections.disclaimer
        ? `\n\nDisclaimer\n${sections.disclaimer}`
        : "",
    ].join("");

    try {
      await navigator.clipboard.writeText(text);

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch {}
  }

  async function handleFeedback(
    rating: "up" | "down"
  ) {
    setFeedbackGiven(rating);

    try {
      if (!sessionId) return;

await sendFeedback(
  sessionId,
  messageId,
  rating
);
    } catch {}
  }

  return (
    <div style={styles.card}>

      <div style={styles.header}>

        <div style={styles.badge}>
          📘 General Legal Information
        </div>

        <h1 style={styles.title}>
          Legal Information
        </h1>

        <p style={styles.subtitle}>
          Educational explanation generated from
          Indian legal sources. This information
          is intended to help you understand the
          law and should not be considered legal
          advice for your specific situation.
        </p>

      </div>

      <div style={styles.article}>

        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{

            h1: ({ children }) => (
              <h1 style={styles.h1}>
                {children}
              </h1>
            ),

            h2: ({ children }) => (
              <h2 style={styles.h2}>
                {children}
              </h2>
            ),

            h3: ({ children }) => (
              <h3 style={styles.h3}>
                {children}
              </h3>
            ),

            p: ({ children }) => (
              <p style={styles.paragraph}>
                {children}
              </p>
            ),

            ul: ({ children }) => (
              <ul style={styles.list}>
                {children}
              </ul>
            ),

            ol: ({ children }) => (
              <ol style={styles.list}>
                {children}
              </ol>
            ),

            li: ({ children }) => (
              <li style={styles.listItem}>
                {children}
              </li>
            ),

            strong: ({ children }) => (
              <strong style={styles.bold}>
                {children}
              </strong>
            ),

            blockquote: ({ children }) => (
              <blockquote
                style={styles.blockquote}
              >
                {children}
              </blockquote>
            ),

            hr: () => (
              <hr style={styles.hr} />
            ),

            code: ({ children }) => (
              <code style={styles.inlineCode}>
                {children}
              </code>
            ),

            pre: ({ children }) => (
              <pre style={styles.pre}>
                {children}
              </pre>
            ),

          }}
        >
          {article}
        </ReactMarkdown>

      </div>
            {sections.sources && (
        <section style={styles.sourcesCard}>

          <button
            style={styles.sourcesButton}
            onClick={() =>
              setSourcesOpen(!sourcesOpen)
            }
          >
            {sourcesOpen
              ? "📚 Hide Sources"
              : "📚 Show Sources"}
          </button>

          {sourcesOpen && (
            <div style={styles.sourcesBody}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
              >
                {sections.sources}
              </ReactMarkdown>
            </div>
          )}

        </section>
      )}

      <footer style={styles.footer}>

        <ConfidenceMeter
          level={confidence}
        />

        <div style={styles.footerRight}>

          <button
            style={styles.copyButton}
            onClick={handleCopy}
          >
            {copied
              ? "✓ Copied"
              : "📋 Copy"}
          </button>

          <button
            disabled={feedbackGiven !== null}
            style={{
              ...styles.feedbackButton,
              opacity:
                feedbackGiven === "down"
                  ? 0.5
                  : 1,
            }}
            onClick={() =>
              handleFeedback("up")
            }
          >
            👍 Helpful
          </button>

          <button
            disabled={feedbackGiven !== null}
            style={{
              ...styles.feedbackButton,
              opacity:
                feedbackGiven === "up"
                  ? 0.5
                  : 1,
            }}
            onClick={() =>
              handleFeedback("down")
            }
          >
            👎 Needs Improvement
          </button>

        </div>

      </footer>

      {sections.disclaimer && (
        <div style={styles.disclaimer}>

          <div
            style={styles.disclaimerTitle}
          >
            ⚠ Disclaimer
          </div>

          <div
            style={styles.disclaimerText}
          >
            {sections.disclaimer}
          </div>

        </div>
      )}

    </div>
  );
}

const styles: Record<
  string,
  React.CSSProperties
> = {

  card: {
    width: "100%",
    maxWidth: 760,
    background: "var(--paper-raised)",
    border: "1px solid var(--line)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow-card)",
    overflow: "hidden",
  },

  header: {
    padding: "28px",
    borderBottom:
      "1px solid var(--line)",
    background:
      "linear-gradient(to bottom,#fbfdff,#ffffff)",
  },

  badge: {
    display: "inline-block",
    background: "#eef6ff",
    color: "var(--ink-navy)",
    padding: "6px 12px",
    borderRadius: 999,
    fontSize: 12,
    fontWeight: 700,
    marginBottom: 18,
  },

  title: {
    margin: 0,
    fontSize: 30,
    fontWeight: 700,
    color: "var(--ink-navy)",
    lineHeight: 1.25,
  },

  subtitle: {
    marginTop: 14,
    marginBottom: 0,
    color: "var(--slate)",
    lineHeight: 1.8,
    fontSize: 15,
  },

  article: {
    padding: 28,
    fontSize: 16,
    lineHeight: 1.9,
    color: "var(--ink-navy)",
  },
    h1: {
    marginTop: 0,
    marginBottom: 20,
    fontSize: 30,
    fontWeight: 700,
    color: "var(--ink-navy)",
    lineHeight: 1.3,
  },

  h2: {
    marginTop: 36,
    marginBottom: 16,
    paddingBottom: 8,
    borderBottom: "1px solid var(--line)",
    fontSize: 24,
    fontWeight: 700,
    color: "var(--ink-navy)",
  },

  h3: {
    marginTop: 28,
    marginBottom: 14,
    fontSize: 20,
    fontWeight: 600,
    color: "var(--ink-navy)",
  },

  paragraph: {
    marginTop: 0,
    marginBottom: 18,
    lineHeight: 1.9,
  },

  list: {
    marginTop: 12,
    marginBottom: 22,
    paddingLeft: 24,
    lineHeight: 1.8,
  },

  listItem: {
    marginBottom: 10,
  },

  bold: {
    fontWeight: 700,
    color: "var(--ink-navy)",
  },

  blockquote: {
    margin: "22px 0",
    padding: "14px 18px",
    borderLeft: "4px solid var(--ink-navy)",
    background: "#f8fbff",
    borderRadius: 10,
    color: "var(--slate)",
    lineHeight: 1.8,
  },

  hr: {
    border: "none",
    borderTop: "1px solid var(--line)",
    margin: "32px 0",
  },

  inlineCode: {
    background: "#f4f4f4",
    padding: "2px 6px",
    borderRadius: 6,
    fontFamily: "monospace",
    fontSize: "0.9em",
  },

  pre: {
    background: "#f8f8f8",
    border: "1px solid var(--line)",
    borderRadius: 10,
    padding: 16,
    overflowX: "auto",
    margin: "20px 0",
    fontFamily: "monospace",
  },

  sourcesCard: {
    margin: "0 28px",
    border: "1px solid var(--line)",
    borderRadius: 12,
    overflow: "hidden",
    background: "var(--paper)",
  },

  sourcesButton: {
    width: "100%",
    padding: "14px 18px",
    border: "none",
    cursor: "pointer",
    background: "transparent",
    textAlign: "left",
    fontSize: 14,
    fontWeight: 600,
    color: "var(--ink-navy)",
  } as React.CSSProperties,

  sourcesBody: {
    padding: "18px",
    borderTop: "1px solid var(--line)",
    lineHeight: 1.8,
    fontSize: 15,
  },

  footer: {
    marginTop: 28,
    padding: "22px 28px",
    borderTop: "1px solid var(--line)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 16,
  },

  footerRight: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    flexWrap: "wrap",
  },

  copyButton: {
    padding: "8px 14px",
    borderRadius: 8,
    border: "1px solid var(--line)",
    background: "#ffffff",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 500,
  },

  feedbackButton: {
    padding: "8px 14px",
    borderRadius: 8,
    border: "1px solid var(--line)",
    background: "#ffffff",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 500,
  },

  disclaimer: {
    margin: "0 28px 28px",
    padding: 18,
    borderRadius: 12,
    borderLeft: "4px solid var(--terracotta)",
    background: "#fff8ef",
  },

  disclaimerTitle: {
    marginBottom: 10,
    fontWeight: 700,
    fontSize: 15,
    color: "var(--ink-navy)",
  },

  disclaimerText: {
    lineHeight: 1.7,
    fontSize: 14,
    color: "var(--slate)",
  },

};