"use client";

const LANGUAGES: { code: string; label: string; native: string }[] = [
  { code: "auto", label: "Auto-detect", native: "" },
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "gu", label: "Gujarati", native: "ગુજરાતી" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ" },
];

export default function LanguageSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (code: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Response language"
      style={styles.select}
    >
      {LANGUAGES.map((l) => (
        <option key={l.code} value={l.code}>
          {l.native ? `${l.native} · ${l.label}` : l.label}
        </option>
      ))}
    </select>
  );
}

const styles: Record<string, React.CSSProperties> = {
  select: {
    fontFamily: "var(--font-ui)",
    fontSize: 14,
    padding: "6px 10px",
    borderRadius: 8,
    border: "1px solid var(--line)",
    background: "var(--paper-raised)",
    color: "var(--ink-navy)",
  },
};
