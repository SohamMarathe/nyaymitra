"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ConfidenceMeter from "./ConfidenceMeter";
import { ResponseSections, sendFeedback } from "@/lib/api";

interface Props {
  sections: ResponseSections;
  confidence: "high" | "medium" | "low" | null;
  sessionId: string;
  messageId: string;
}

function Section({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  if (!children) return null;

  return (
    <section style={styles.section}>
      <div style={styles.sectionHeader}>
        {label}
      </div>

      <div style={styles.sectionBody}>
        {children}
      </div>
    </section>
  );
}

export default function ResponseCard({ sections, confidence, sessionId, messageId }: Props) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<"up" | "down" | null>(null);
  const [copied, setCopied] = useState(false);
  const handleFeedback = async (rating: "up" | "down") => {
    setFeedbackGiven(rating);
    try {
      await sendFeedback(sessionId, messageId, rating);
    } catch {
      // Non-critical — feedback failing silently shouldn't interrupt the user.
    }
  };

  const handleCopy = async () => {
  const text = [
  "Summary",
  sections.summary,

  "Applicable Law",
  sections.law,

  "What this means",
  sections.situation,

  "Next Steps",
  sections.next_steps,

  sections.note ? `Important Note\n${sections.note}` : "",

  sections.sources ? `Sources\n${sections.sources}` : "",

  sections.disclaimer ? `Disclaimer\n${sections.disclaimer}` : "",
]
.filter(Boolean)
.join("\n\n");

  try {
    await navigator.clipboard.writeText(text);
    setCopied(true);

    setTimeout(() => setCopied(false), 2000);
  } catch {}
};

  return (
    <div style={styles.card}>
      <Section label="Summary"><div style={styles.markdown}><ReactMarkdown remarkPlugins={[remarkGfm]}>{sections.summary}</ReactMarkdown></div></Section> 
      <Section label="Your rights / applicable law"><div style={styles.markdown}><ReactMarkdown remarkPlugins={[remarkGfm]}>{sections.law}</ReactMarkdown></div></Section>
      <Section label="What this means for your situation"><div style={styles.markdown}><ReactMarkdown remarkPlugins={[remarkGfm]}>{sections.situation}</ReactMarkdown></div></Section>
      <Section label="What you can do next"><div style={styles.markdown}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
        >
          {sections.next_steps}
        </ReactMarkdown></div>
      </Section>
      {sections.note && <Section label="Important note"><div style={styles.markdown}><ReactMarkdown remarkPlugins={[remarkGfm]}>{sections.note}</ReactMarkdown></div></Section>}

      {sections.sources && (
        <div style={styles.sourcesBlock}>
          <button style={styles.sourcesToggle} onClick={() => setSourcesOpen((v) => !v)}>
            {sourcesOpen ? "📚 Hide Sources" : "📚 Show Sources"}
          </button>
          {sourcesOpen && <div style={{ ...styles.sectionBody, marginTop: 8 }}><div style={styles.markdown}><ReactMarkdown remarkPlugins={[remarkGfm]}>{sections.sources}</ReactMarkdown></div></div>}
        </div>
      )}

      <div style={styles.footer}>

        <ConfidenceMeter level={confidence} />

        <div style={styles.footerActions}>

          <button
            style={styles.copyBtn}
            onClick={handleCopy}
          >
            {copied ? "✓ Copied" : "📋 Copy"}
          </button>

          <div style={styles.feedbackRow}>

            <button
              disabled={feedbackGiven !== null}
              onClick={() => handleFeedback("up")}
              style={{
                ...styles.feedbackBtn,
                opacity: feedbackGiven === "down" ? .4 : 1,
              }}
            >
              👍 Helpful
            </button>

            <button
              disabled={feedbackGiven !== null}
              onClick={() => handleFeedback("down")}
              style={{
                ...styles.feedbackBtn,
                opacity: feedbackGiven === "up" ? .4 : 1,
              }}
            >
              👎 Needs improvement
            </button>

          </div>

        </div>

      </div>

      {sections.disclaimer && <div style={styles.disclaimer}><>
<strong>⚠ Legal Disclaimer</strong>

<div style={{ marginTop: 6 }}>
  {sections.disclaimer}
</div>
</></div>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    background: "var(--paper-raised)",
    border: "1px solid var(--line)",
    borderRadius: "var(--radius)",
    boxShadow: "var(--shadow-card)",
    padding: "18px 20px",
    maxWidth: 760,
    width: "100%",
  },
  section: {
  border: "1px solid var(--line)",
  borderRadius: 12,
  padding: 14,
  marginBottom: 14,
  background: "var(--paper)",
},

sectionHeader: {

    fontWeight:700,

    marginBottom:10,

    color:"var(--ink-navy)",

    fontSize:15,

},
  
  sectionBody: {

    fontSize:15,

    lineHeight:1.7,

    color:"var(--ink-navy)",

},
footerActions:{

display:"flex",

alignItems:"center",

gap:12,

},

copyBtn:{

border:"1px solid var(--line)",

background:"white",

borderRadius:8,

padding:"6px 10px",

fontSize:13,

cursor:"pointer",

},

  sourcesBlock: { marginBottom: 14 },
  sourcesToggle: {
    background: "none",
    border: "1px solid var(--line)",
    borderRadius: 8,
    padding: "4px 10px",
    fontSize: 13,
    color: "var(--ink-navy-soft)",
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 10,
    paddingTop: 10,
    borderTop: "1px solid var(--line)",
  },
  feedbackRow: { display: "flex", gap: 6 },
  feedbackBtn:{

border:"1px solid var(--line)",

borderRadius:8,

background:"white",

padding:"6px 10px",

cursor:"pointer",

fontSize:13,

},

markdown: {
  fontSize: 15,
  lineHeight: 1.8,
},

  disclaimer:{

marginTop:16,

padding:12,

borderRadius:10,

background:"#fff8ef",

borderLeft:"4px solid var(--terracotta)",

fontSize:13,

lineHeight:1.6,

color:"var(--slate)",

},
};
