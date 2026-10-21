"use client";

type Confidence = "high" | "medium" | "low" | null | undefined;

const LEVELS: { key: Confidence; label: string; color: string }[] = [
  { key: "low", label: "Low", color: "var(--terracotta)" },
  { key: "medium", label: "Medium", color: "var(--seal-gold)" },
  { key: "high", label: "High", color: "var(--banyan-green)" },
];

const FILLED_COUNT: Record<string, number> = { low: 1, medium: 2, high: 3 };

/**
 * Three segments, filled left-to-right by confidence level. This is drawn
 * directly from the Reasoning & Validation Agent's actual output — not a
 * decorative progress bar — so it's an honest signal, not a UI flourish.
 */
export default function ConfidenceMeter({ level }: { level: Confidence }) {
  if (!level) return null;
  const filled = FILLED_COUNT[level] ?? 0;
  const active = LEVELS.find((l) => l.key === level);

  return (
    <div style={styles.wrap} aria-label={`Confidence: ${active?.label ?? level}`}>
      <div style={styles.segments}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              ...styles.segment,
              background: i < filled ? active?.color : "var(--line)",
            }}
          />
        ))}
      </div>
      <span style={{ ...styles.label, color: active?.color }}>{active?.label} confidence</span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrap: { display: "flex", alignItems: "center", gap: 8, marginTop: 4 },
  segments: { display: "flex", gap: 3 },
  segment: { width: 18, height: 5, borderRadius: 3, display: "inline-block" },
  label: { fontSize: 12, fontWeight: 600, letterSpacing: 0.2 },
};
