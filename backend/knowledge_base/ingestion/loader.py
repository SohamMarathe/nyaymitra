"""
Reads raw documents (PDFs downloaded manually from official sources, or
.txt files you typed/pasted yourself) into plain text, ready for chunking.

Nothing here touches the network. You download PDFs by hand once (see
knowledge_base_raw/README.md for exactly what to get and from where) and
this just parses what's already on disk.
"""
import pdfplumber
from pathlib import Path


def load_pdf(path: Path) -> str:
    """pdfplumber handles the multi-column, table-heavy layout of Indian
    government PDFs noticeably better than PyPDF2/pypdf for this use case."""
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix in (".txt", ".md"):
        return load_text(path)
    raise ValueError(f"Unsupported file type: {path}")


def find_documents(domain_dir: Path) -> list[dict]:
    """Walks acts/procedures/judgments/faqs subfolders and returns a list of
    {path, domain, chunk_type} ready for loading. chunk_type comes straight
    from the subfolder name, which is the whole point of that structure."""
    domain = domain_dir.name
    docs = []
    for chunk_type_dir in domain_dir.iterdir():
        if not chunk_type_dir.is_dir():
            continue
        chunk_type = chunk_type_dir.name  # acts | procedures | judgments | faqs
        for file_path in chunk_type_dir.glob("*"):
            if file_path.suffix.lower() in (".pdf", ".txt", ".md"):
                docs.append({"path": file_path, "domain": domain, "chunk_type": chunk_type.rstrip("s")})
    return docs
