# Design Decisions & Rationale

This document exists because architecture diagrams show *what* was built,
not *why*. The "why" is what an interviewer actually probes — anyone can
draw five boxes and an arrow between them; being able to defend each box
is what separates a real system-design exercise from a template.

---

## Why LangGraph instead of a separate Supervisor Agent

A Supervisor Agent pattern adds an LLM call whose only job is deciding
which other agent to call next. For a pipeline where the *order* of agents
is already well-defined (scope check → intent → retrieval → reasoning →
response), that decision doesn't need intelligence — it needs a
conditional edge. LangGraph's `StateGraph` gives us conditional routing,
a shared typed state object, and (if we ever wanted it) built-in
checkpointing, all without spending an API call on "what should happen
next" when the answer is almost always "the next fixed step, unless X."

The one place real routing intelligence is needed — does this query need
a follow-up question or not — lives inside the Intent Agent itself
(`route_after_intent`), which already has the context to decide. That's an
`if/else` on data the Intent Agent already produced, not a separate agent.

## Why domain-specific FAISS collections instead of retrieval sub-agents

Two ways to get "search only Consumer law": (a) one Retrieval Agent that
looks up which collection to search based on the domain, or (b) six
separate Retrieval *Agents*, one per domain, each an LLM call. (b) spends
model calls choosing between indexes — something a plain dictionary
lookup does perfectly (`domain -> {domain}.index`). Splitting the
*knowledge base* by domain is valuable (it keeps searches precise and
indexes small); splitting the *agent* by domain is not, because selecting
an index isn't a reasoning task.

## Why Reasoning and Validation were merged into one agent

Early drafts had these separate. In practice, "generate a grounded answer"
and "check that answer only says what the sources support" are the same
skill applied twice to the same context (the retrieved chunks + the
question) — splitting them into two agents would mean passing the exact
same sources to two different LLM calls with only the second prompt
differing. Instead, `reasoning_agent.py` does two *calls* (draft, then
self-audit) inside one *agent*, keeping the two passes tightly coupled to
the same context without the overhead of a separate node, its own prompt
file, and its own place in the graph for what's really one responsibility:
"produce a legally grounded, self-checked answer."

## Why the Response Agent owns both translation and simplification

Both are the same underlying task — take the same meaning and express it
differently for the reader — just varying on which axis (language vs.
register). Splitting them into a Translation Agent and a Simplification
Agent would mean running an LLM call, then running a second LLM call on
its output, doubling latency and cost for two changes that are cheaper and
more coherent to make together: a model asked to "explain this simply, in
Marathi" produces more natural output in one pass than a model asked to
simplify in English and a second model asked to translate that
already-simplified text, which tends to read stiffly translated rather
than natively written.

---

## Decisions made during implementation (not just design)

These came up once actual code had to be written, which is exactly the
kind of thing that doesn't show up in an architecture diagram but matters
in an interview.

**Dropped LangChain as a dependency.** The original stack listed
LangChain alongside LangGraph. Once building started, every agent turned
out to need exactly one thing from an LLM library: "call the model, get
text or structured JSON back." LangChain's chains/retrievers/output-parsers
add a real abstraction layer for that — useful at larger scale, mostly
indirection here. Each agent calls `google-genai` directly through a
~100-line shared wrapper (`agents/llm_client.py`) with retry/backoff and
JSON-schema enforcement built in. Fewer dependencies to version-match,
fewer places for a beginner to get lost debugging someone else's
abstraction instead of their own logic.

**Skipped LangGraph's built-in checkpointer.** LangGraph can persist state
between turns automatically via `langgraph-checkpoint-postgres`, but that
means learning its schema and async setup on top of everything else. Since
only a handful of fields actually need to survive between turns
(`PERSISTED_FIELDS` in `graph/state.py`), we persist those ourselves as a
JSON column on the `sessions` table. A few more explicit lines, but every
part of it is visible in code you wrote and can step through, instead of
inside a library's internals.

**Model tiering.** Classification-shaped steps (scope check, intent,
follow-up question generation) use `gemini-3.1-flash-lite` — fast, cheap,
plenty for "which of six domains is this." The two steps where getting it
wrong actually matters — grounding and self-auditing an answer, and
producing the final response — use the stronger `gemini-3.5-flash`. This
is a genuine cost/quality tradeoff, not just "use the biggest model
everywhere," and it's a decision worth being able to explain out loud.

**Section-based chunking over character-count chunking.** Covered in
`knowledge_base_raw/README.md` and `chunker.py` directly, but worth
repeating here: a RAG system's retrieval quality is bounded by its
chunking strategy long before it's bounded by its embedding model or its
LLM. This is the least glamorous part of the system and the part most
likely to silently determine whether the whole thing actually works.

---

## What's intentionally NOT built (and why that's a decision too)

- **No document upload.** Real privacy liability under India's DPDP Act
  for something that adds little value to an *information* tool (as
  opposed to a case-management tool).
- **No legal notice drafting.** Generating legal documents edges toward
  practicing law, not informing about it — a line worth staying well
  clear of.
- **No case outcome prediction**, ever, in any phase. Legally irresponsible
  and impossible to defend as "information" rather than "advice."
- **No Supervisor Agent, no per-domain retrieval agents** — covered above.

A resume-worthy project isn't the one with the most agents. It's the one
where every agent's existence can be defended in one sentence.
