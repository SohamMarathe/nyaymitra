const API_BASE =
(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export interface ResponseSections {
  summary: string;
  law: string;
  situation: string;
  next_steps: string;
  note: string;
  sources: string;
  confidence_line: string;
  disclaimer: string;
  raw: string;
}

export interface QueryResponse {
  session_id: string;
  message_id: string;
  response_text: string;
  sections: ResponseSections;
  confidence: "high" | "medium" | "low" | null;
  awaiting_reply: boolean;
  response_mode: "plain" | "structured";
}

export async function sendQuery(
  message: string,
  sessionId: string | null,
  language: string | null
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, language }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Query failed (${res.status}): ${detail}`);
  }
  return (await res.json()) as QueryResponse;
}

export async function sendFeedback(
  sessionId: string,
  messageId: string,
  rating: "up" | "down"
): Promise<void> {
  await fetch(`${API_BASE}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, rating }),
  });
}
