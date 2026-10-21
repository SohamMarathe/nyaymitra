# Knowledge Base — Raw Documents

This folder is empty in git on purpose (see root `.gitignore`) — you populate
it yourself by manually downloading official documents, then run ingestion
to build the FAISS indexes.

## Why manual download instead of scraping

Government legal portals increasingly block automated scraping (anti-bot
protection, rate limits, CAPTCHAs), and it's unnecessary here anyway: laws
don't change daily like news does, so a one-time manual download per
document is both more reliable and legally cleaner than scraping. You click
download once; the ingestion pipeline handles everything after that.

## Folder structure (per domain)

```
<domain>/
├── acts/          → full bare acts, PDF, from official sources
├── procedures/     → step-by-step procedural guides, .txt (copy-paste + clean up)
├── judgments/       → key excerpts from landmark judgments, .txt (copy-paste)
└── faqs/            → plain-language Q&A, .txt (you can write these yourself)
```

## Filename convention — READ THIS, it matters

`chunker.py` parses the **source name and year directly from the filename**.
Name files like this:

```
consumer_protection_act_2019.pdf   → source: "Consumer Protection Act", year: "2019"
code_on_wages_2019.pdf              → source: "Code On Wages",          year: "2019"
it_act_2000.pdf                       → source: "It Act",                 year: "2000"
```

Rule: lowercase words separated by underscores, ending in the 4-digit year.
If a filename doesn't end in a 4-digit year, ingestion still works — it
just won't have a precise year for citations.

For `.txt` files (procedures, judgments, faqs), the same convention applies
— name them descriptively, e.g. `ncdrc_deficiency_of_service_2021.txt`.

## Per-domain source lists

See `README.md` inside each domain folder for exact links and what to
download for that domain. Start with **consumer** — it has the clearest
procedures and is the recommended Phase 0/1 domain.

## A critical, easy-to-miss correction

India's core criminal statutes were **replaced** in 2023–2024:

| Old (repealed)                 | New (current law)                        |
|---------------------------------|--------------------------------------------|
| Indian Penal Code, 1860 (IPC)     | Bharatiya Nyaya Sanhita, 2023 (BNS)         |
| Code of Criminal Procedure, 1973 (CrPC) | Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) |
| Indian Evidence Act, 1872         | Bharatiya Sakshya Adhiniyam, 2023 (BSA)      |

If you build the Criminal domain (Phase 2+), download the **BNS/BNSS/BSA**,
not IPC/CrPC/Evidence Act — a huge amount of content online (tutorials,
old PDFs, even some government pages not yet updated) still references the
old Acts.

## A second one — labour law changed too, more recently

The four new **Labour Codes** (Code on Wages 2019, Industrial Relations
Code 2020, Code on Social Security 2020, Occupational Safety Health &
Working Conditions Code 2020) came into force nationwide on **21 November
2025**, repealing 29 older central laws including the Payment of Wages
Act 1936, Minimum Wages Act 1948, Industrial Disputes Act 1947, and
Factories Act 1948.

Unlike the criminal-law swap above, this one is genuinely messy: central
and most state *implementing rules* are still being finalized
state-by-state, so old-Act provisions continue to apply wherever new
rules haven't caught up yet. See `labour/README.md` for exactly what this
means for what you download. This is worth getting right for the same
reason as BNS/BNSS/BSA — a legal-information tool citing repealed law as
current is the single easiest way to quietly mislead someone.

Getting either of these wrong in a legal-information tool is the easiest
way to silently give someone outdated law, so it's worth the extra care.

## After downloading — run ingestion

```bash
python -m backend.knowledge_base.ingestion.run_ingestion --domain consumer
```

Then test retrieval in isolation (do this before touching the agents):

```bash
python -m backend.scripts.test_retrieval consumer "how do I file a complaint about a defective product"
```
