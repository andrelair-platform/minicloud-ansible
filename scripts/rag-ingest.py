#!/usr/bin/env python3
"""
rag-ingest.py — Structure-aware RAG ingestion pipeline for minicloud.

Routes documents through Docling (PDF/scanned) or MarkItDown (Office formats),
splits at structural boundaries (Article/Annexe/Chapitre/Section), attaches
rich insurance metadata, embeds via bge-m3 on Ollama, and stores directly in
ragdb.document_chunk so Open WebUI can query the chunks.

Usage
-----
  # 1. Activate port-forwards (run each in a separate terminal or background them)
  kubectl port-forward -n ai svc/docling    5001:5001 &
  kubectl port-forward -n ai svc/ollama     11434:11434 &
  kubectl port-forward -n ai postgresql-ai-0 5432:5432 &

  # 2. Get the PostgreSQL password
  PG_PASS=$(kubectl get secret -n ai ai-postgresql-secret \
    -o jsonpath='{.data.password}' | base64 -d)

  # 3. Create a Knowledge Base in Open WebUI and note its UUID
  #    Workspace → Knowledge → New Knowledge Base → copy UUID from URL

  # 4. Run the script
  python3 rag-ingest.py \\
    --file contrat_rc_pro.pdf \\
    --collection <open-webui-kb-uuid> \\
    --doc-type policy \\
    --source "Contrat RC Pro 2026" \\
    --pg-pass "$PG_PASS"

Dependencies
------------
  pip install requests psycopg2-binary markitdown
  (Docling and Ollama are accessed via HTTP — no local install needed)
"""

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path

import psycopg2
import requests

# ── Defaults (override via env vars or CLI flags) ──────────────────────────────
DOCLING_URL  = os.getenv("DOCLING_URL",  "http://localhost:5001")
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")
PG_HOST      = os.getenv("PG_HOST",      "localhost")
PG_PORT      = int(os.getenv("PG_PORT",  "5432"))
PG_DB        = os.getenv("PG_DB",        "ragdb")
PG_USER      = os.getenv("PG_USER",      "aiplatform")
EMBED_MODEL  = "bge-m3"

# ── Document type vocabulary (for metadata) ────────────────────────────────────
DOC_TYPES = ["policy", "endorsement", "annexe", "regulatory", "tariff", "internal"]

# ── Structure detection: French insurance heading patterns ─────────────────────
# Matches: "Article 12.3 — Exclusions", "## Annexe B - Tableau", "CHAPITRE II"
HEADING_RE = re.compile(
    r'^(?:#{1,4}\s+)?'
    r'(Article|Chapitre|Titre|Annexe|Section|Garantie|Disposition'
    r'|ARTICLE|CHAPITRE|TITRE|ANNEXE|SECTION)'
    r'(?:\s+[\dA-Za-z]+(?:[.\-]\d+)*)?'
    r'(?:\s*[-–—:]\s*(.+))?',
    re.IGNORECASE,
)

# Also treat markdown headings as structural breaks even without keywords
MD_HEADING_RE = re.compile(r'^#{1,3}\s+.+', re.MULTILINE)

MAX_CHUNK_CHARS = 2000  # fallback split threshold if a structural section is huge


# ── Conversion ─────────────────────────────────────────────────────────────────

def convert_to_markdown(file_path: Path) -> str:
    """Route to Docling (PDF) or MarkItDown (Office) based on extension."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _docling_convert(file_path)

    if suffix in {".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".html", ".htm"}:
        return _markitdown_convert(file_path)

    if suffix in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8")

    raise ValueError(f"Unsupported format: {suffix}. Add to the router if needed.")


def _docling_convert(file_path: Path) -> str:
    print(f"  → Docling: converting {file_path.name}...")
    with open(file_path, "rb") as f:
        resp = requests.post(
            f"{DOCLING_URL}/v1/convert/file",
            files={"file": (file_path.name, f, "application/pdf")},
            timeout=300,
        )
    resp.raise_for_status()
    data = resp.json()
    md = data.get("document", {}).get("md_content") or data.get("content", "")
    if not md:
        raise RuntimeError(f"Docling returned no content: {data}")
    print(f"     {len(md):,} chars of markdown")
    return md


def _markitdown_convert(file_path: Path) -> str:
    print(f"  → MarkItDown: converting {file_path.name}...")
    try:
        from markitdown import MarkItDown
    except ImportError:
        raise ImportError("Install markitdown: pip install markitdown")
    md = MarkItDown().convert(str(file_path)).text_content
    print(f"     {len(md):,} chars of markdown")
    return md


# ── Structure-aware chunking ───────────────────────────────────────────────────

def chunk_by_structure(markdown: str, source: str, doc_type: str, extra_meta: dict) -> list[dict]:
    """
    Split markdown at structural headings (Article/Annexe/Section/##).
    Each chunk carries the section it belongs to as metadata.
    Falls back to paragraph splitting if a section exceeds MAX_CHUNK_CHARS.
    """
    lines = markdown.splitlines()
    sections = []
    current_heading = "Préambule"
    current_lines = []

    for line in lines:
        is_heading = HEADING_RE.match(line.strip()) or (
            MD_HEADING_RE.match(line) and len(line.strip()) > 4
        )
        if is_heading and current_lines:
            sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line.strip().lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    chunks = []
    for heading, text in sections:
        if not text:
            continue
        # If the section is small enough, keep it whole
        if len(text) <= MAX_CHUNK_CHARS:
            chunks.append(_make_chunk(text, heading, source, doc_type, extra_meta))
        else:
            # Fallback: split large sections on paragraph boundaries
            paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
            buffer = ""
            for para in paragraphs:
                if len(buffer) + len(para) + 2 <= MAX_CHUNK_CHARS:
                    buffer = (buffer + "\n\n" + para).strip()
                else:
                    if buffer:
                        chunks.append(_make_chunk(buffer, heading, source, doc_type, extra_meta))
                    buffer = para
            if buffer:
                chunks.append(_make_chunk(buffer, heading, source, doc_type, extra_meta))

    return chunks


def _make_chunk(text: str, section: str, source: str, doc_type: str, extra_meta: dict) -> dict:
    # Extract article number from section heading if present
    article_match = re.search(
        r'(Article|Annexe|Section|Chapitre)\s+([\dA-Za-z]+(?:[.\-]\d+)*)',
        section, re.IGNORECASE
    )
    article_ref = article_match.group(0) if article_match else None

    metadata = {
        "document_type": doc_type,
        "section": section,
        "source": source,
        **extra_meta,
    }
    if article_ref:
        metadata["article"] = article_ref

    return {"text": text, "metadata": metadata}


# ── Embedding ──────────────────────────────────────────────────────────────────

def embed(text: str) -> list[float]:
    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


# ── Storage ────────────────────────────────────────────────────────────────────

def store_chunks(chunks: list[dict], collection: str, pg_pass: str):
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=pg_pass,
    )
    cur = conn.cursor()

    inserted = 0
    for i, chunk in enumerate(chunks):
        print(f"  embedding chunk {i+1}/{len(chunks)}: {chunk['metadata'].get('section','')[:60]}...")
        vector = embed(chunk["text"])
        chunk_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO document_chunk (id, collection_name, text, vector, vmetadata)
            VALUES (%s, %s, %s, %s::vector, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                chunk_id,
                collection,
                chunk["text"],
                json.dumps(vector),
                json.dumps(chunk["metadata"]),
            ),
        )
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    return inserted


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Structure-aware RAG ingestion for minicloud")
    parser.add_argument("--file",       required=True,  help="Path to document (PDF/DOCX/XLSX/PPTX/MD)")
    parser.add_argument("--collection", required=True,  help="Open WebUI Knowledge Base UUID")
    parser.add_argument("--doc-type",   default="policy", choices=DOC_TYPES, help="Document type")
    parser.add_argument("--source",     required=True,  help="Human-readable document name")
    parser.add_argument("--pg-pass",    default=os.getenv("PG_PASS", ""), help="ragdb password")
    parser.add_argument("--page",       type=int, default=None, help="Starting page number (optional)")
    args = parser.parse_args()

    if not args.pg_pass:
        sys.exit("Error: --pg-pass required (or set PG_PASS env var)")

    file_path = Path(args.file)
    if not file_path.exists():
        sys.exit(f"Error: file not found: {file_path}")

    extra_meta = {"source": args.source, "doc_type": args.doc_type}
    if args.page:
        extra_meta["page_start"] = args.page

    print(f"\n[1/4] Converting {file_path.name}")
    markdown = convert_to_markdown(file_path)

    print(f"\n[2/4] Chunking by document structure")
    chunks = chunk_by_structure(markdown, args.source, args.doc_type, extra_meta)
    print(f"      {len(chunks)} structural chunks")
    for c in chunks[:5]:
        print(f"      • {c['metadata'].get('section','?')[:70]} ({len(c['text'])} chars)")
    if len(chunks) > 5:
        print(f"      ... and {len(chunks)-5} more")

    print(f"\n[3/4] Embedding + storing in ragdb (collection: {args.collection})")
    inserted = store_chunks(chunks, args.collection, args.pg_pass)

    print(f"\n[4/4] Done — {inserted} chunks stored")
    print(f"      In Open WebUI: open the Knowledge Base, it will query these chunks automatically.")
    print(f"\nMetadata sample:")
    print(json.dumps(chunks[0]["metadata"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
