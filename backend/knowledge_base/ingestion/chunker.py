"""
Chunks legal text by LEGAL UNIT, not by character count.

Character-count chunking will slice "Section 138 of the Negotiable
Instruments Act states that..." mid-sentence and hand the Retrieval Agent
fragments that don't correspond to anything a lawyer would call a unit of
law. Section-aware chunking gives it something legally coherent instead.

Filename convention this relies on (document this in your own downloads too):
    <act_name_with_underscores>_<year>.pdf
    e.g. consumer_protection_act_2019.pdf  -> source="Consumer Protection Act", year="2019"
    e.g. code_on_wages_2019.pdf            -> source="Code On Wages", year="2019"
If a filename doesn't end in a 4-digit year, source becomes the whole
filename and year is left as "n.d." — still usable, just less precise
in citations.
"""
import re
from pathlib import Path

_SECTION_SPLIT_RE = re.compile(
    r"\n(?=(?:Section|SECTION)\s+\d+[A-Za-z]?\b|\n?\d{1,3}[A-Za-z]?\.\s+[A-Z])"
)
_SECTION_NUMBER_RE = re.compile(r"(?:Section|SECTION)\s+(\d+[A-Za-z]?)|^(\d{1,3}[A-Za-z]?)\.")

_MAX_PROSE_CHUNK_CHARS = 1500
_MIN_CHUNK_CHARS = 40


def _parse_filename_metadata(path: Path) -> tuple[str, str]:
    stem = path.stem  # filename without extension
    parts = stem.split("_")
    if parts and re.fullmatch(r"\d{4}", parts[-1]):
        year = parts[-1]
        source = " ".join(p.capitalize() for p in parts[:-1])
    else:
        year = "n.d."
        source = " ".join(p.capitalize() for p in parts)
    return source, year


def _extract_section_number(text: str) -> str:
    match = _SECTION_NUMBER_RE.search(text[:120])
    if match:
        num = match.group(1) or match.group(2)
        return f"Section {num}"
    return "General"


def chunk_act_text(text: str) -> list[str]:
    """Splits on 'Section N' / numbered-clause markers. Falls back to the
    whole text as one chunk if no markers are found (some acts, especially
    short amendment notifications, don't use 'Section N' formatting)."""
    pieces = _SECTION_SPLIT_RE.split(text)
    chunks = [p.strip() for p in pieces if len(p.strip()) >= _MIN_CHUNK_CHARS]
    return chunks or ([text.strip()] if text.strip() else [])


def chunk_prose_text(text: str) -> list[str]:
    """For judgments/procedures/FAQs — chunk by paragraph, merging short
    paragraphs together up to a size cap so retrieval doesn't return a
    one-line fragment stripped of its context."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) <= _MAX_PROSE_CHUNK_CHARS:
            buffer = f"{buffer}\n\n{para}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            buffer = para
    if buffer:
        chunks.append(buffer)
    return [c for c in chunks if len(c) >= _MIN_CHUNK_CHARS]


def chunk_document(text: str, path: Path, domain: str, chunk_type: str) -> list[dict]:
    source, year = _parse_filename_metadata(path)
    raw_chunks = chunk_act_text(text) if chunk_type == "act" else chunk_prose_text(text)

    result = []
    for raw in raw_chunks:
        result.append({
            "text": raw,
            "source": source,
            "section": _extract_section_number(raw) if chunk_type == "act" else "N/A",
            "domain": domain,
            "chunk_type": chunk_type,
            "year": year,
        })
    return result
