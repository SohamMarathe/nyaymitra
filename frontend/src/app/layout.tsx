import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NyayaMitra — Legal Information, Simply Explained",
  description:
    "An agentic AI assistant that helps Indian citizens understand their legal rights and procedures in their own language.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/*
          Loaded as a plain <link> rather than next/font/google, because each
          Indic script is a SEPARATE font family in Google Fonts (there is no
          single "Noto Sans" covering Devanagari + Bengali + Tamil + Telugu +
          Gujarati + Kannada in one file) — requesting them together here and
          listing them all in the CSS font-family stack (see globals.css) is
          the simplest reliable way to get correct multi-script fallback.
        */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&family=Noto+Serif:wght@600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Bengali:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;500;600;700&family=Noto+Sans+Telugu:wght@400;500;600;700&family=Noto+Sans+Gujarati:wght@400;500;600;700&family=Noto+Sans+Kannada:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
