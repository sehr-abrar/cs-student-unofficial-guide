"""
ingest.py — Document loading and chunking pipeline (Milestone 3)

Loads all .txt files from documents/, cleans them, and splits them into
overlapping character-level chunks ready for embedding.

Spec: chunk_size=400 chars, chunk_overlap=50 chars (see planning.md).
"""

import os
import re
import random


DOCUMENTS_DIR = "documents"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50


def load_documents(directory: str = DOCUMENTS_DIR) -> list[dict]:
    """Read every .txt file in directory. Returns list of {text, source}."""
    docs = []
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(directory, filename)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        docs.append({"text": raw, "source": filename})
    return docs


def clean_text(text: str) -> str:
    """
    Light cleaning for plain-text documents:
    - Normalize line endings
    - Collapse runs of blank lines to a single blank line
    - Strip leading/trailing whitespace per line
    - Remove the two-line file header (Source: / URL: lines)
    """
    lines = text.replace("\r\n", "\n").split("\n")

    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Drop metadata header lines and markdown horizontal rules
        if stripped.startswith("Source:") or stripped.startswith("URL:"):
            continue
        if re.fullmatch(r"-{3,}", stripped):
            continue
        cleaned.append(stripped)

    # Collapse 3+ consecutive blank lines into 2
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned))
    return result.strip()


def chunk_text(text: str, source: str,
               chunk_size: int = CHUNK_SIZE,
               chunk_overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Split text into overlapping character-level chunks.

    Works like LangChain's CharacterTextSplitter: advance through the text by
    (chunk_size - chunk_overlap) characters each step so the tail of one chunk
    appears at the head of the next, preserving sentences that straddle a
    boundary.
    """
    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"text": chunk, "source": source})
        start += step

    return chunks


def build_chunks(documents: list[dict]) -> list[dict]:
    """Clean and chunk every document. Returns flat list of chunk dicts."""
    all_chunks = []
    for doc in documents:
        cleaned = clean_text(doc["text"])
        chunks = chunk_text(cleaned, source=doc["source"])
        all_chunks.extend(chunks)
    return all_chunks


def inspect_chunks(chunks: list[dict], n: int = 5) -> None:
    """Print n random chunks with their source and index for manual review."""
    sample = random.sample(chunks, min(n, len(chunks)))
    print(f"\n{'='*60}")
    print(f"CHUNK INSPECTION — {n} random samples")
    print(f"{'='*60}")
    for i, chunk in enumerate(sample, 1):
        print(f"\n--- Chunk {i} | source: {chunk['source']} ---")
        print(chunk["text"])
    print(f"\n{'='*60}")


if __name__ == "__main__":
    print("Loading documents...")
    documents = load_documents()
    print(f"  Loaded {len(documents)} documents")

    print("\nCleaning and chunking...")
    chunks = build_chunks(documents)
    print(f"  Total chunks: {len(chunks)}")

    per_doc = {}
    for c in chunks:
        per_doc[c["source"]] = per_doc.get(c["source"], 0) + 1
    print("\nChunks per document:")
    for source, count in per_doc.items():
        print(f"  {source}: {count}")

    inspect_chunks(chunks, n=5)

    # Sanity checks
    empty = [c for c in chunks if not c["text"].strip()]
    if empty:
        print(f"\nWARNING: {len(empty)} empty chunks found — check cleaning logic")
    else:
        print("\nAll chunks non-empty.")

    lengths = [len(c["text"]) for c in chunks]
    print(f"Chunk length stats: min={min(lengths)}, max={max(lengths)}, "
          f"avg={sum(lengths)//len(lengths)}")
