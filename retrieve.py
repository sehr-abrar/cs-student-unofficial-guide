"""
retrieve.py — Embedding, vector store, and retrieval (Milestone 4)

Embeds chunks produced by ingest.py using all-MiniLM-L6-v2, stores them
in a local ChromaDB collection with source metadata, and exposes a
retrieve() function that returns the top-k most relevant chunks for
any query string.

Run this file directly to build the vector store and test retrieval:
    python retrieve.py
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import build_chunks, load_documents


CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "cs_guide"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 4

# Module-level singletons so callers (e.g. generate.py) reuse the same
# loaded model and client without re-initialising on every call.
_model: SentenceTransformer | None = None
_collection: chromadb.Collection | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def _get_collection(persist_dir: str = CHROMA_DIR) -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=persist_dir)
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def embed_and_store(chunks: list[dict], persist_dir: str = CHROMA_DIR) -> int:
    """
    Embed every chunk and upsert into ChromaDB.

    Each chunk gets:
        id       — "{source}_{index}" (unique, stable across reruns)
        embedding — float vector from all-MiniLM-L6-v2
        document  — the raw chunk text (ChromaDB stores this for retrieval)
        metadata  — {"source": filename, "chunk_index": int}

    Returns the total number of chunks stored.
    """
    model = _get_model()
    collection = _get_collection(persist_dir)

    texts = [c["text"] for c in chunks]
    sources = [c["source"] for c in chunks]

    print(f"  Embedding {len(texts)} chunks with {EMBED_MODEL_NAME}...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    ids = [f"{src}_{i}" for i, src in enumerate(sources)]
    metadatas = [
        {"source": src, "chunk_index": i}
        for i, src in enumerate(sources)
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    return collection.count()


def retrieve(query: str, k: int = TOP_K, persist_dir: str = CHROMA_DIR) -> list[dict]:
    """
    Embed query and return the top-k most similar chunks.

    Each result dict contains:
        text     — chunk content
        source   — source filename
        distance — cosine distance (lower = more similar; 0.0 = identical)
    """
    model = _get_model()
    collection = _get_collection(persist_dir)

    query_embedding = model.encode([query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text": doc,
            "source": meta["source"],
            "distance": round(dist, 4),
        })
    return hits


def print_results(query: str, hits: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")
    for i, hit in enumerate(hits, 1):
        print(f"\n[{i}] source: {hit['source']}  |  distance: {hit['distance']}")
        print(hit["text"])


if __name__ == "__main__":
    # ── Build vector store ──────────────────────────────────────────────
    print("Loading and chunking documents...")
    chunks = build_chunks(load_documents())
    print(f"  {len(chunks)} chunks ready")

    print("\nBuilding vector store...")
    total = embed_and_store(chunks)
    print(f"  Vector store contains {total} chunks")

    # ── Test retrieval with 3 evaluation-plan queries ───────────────────
    test_queries = [
        "What do students say about Prof. Chen's office hours in Algorithms?",
        "What is the recruiting timeline for big tech summer internships?",
        "Can I use AI tools like GitHub Copilot on my CS assignments?",
    ]

    for query in test_queries:
        hits = retrieve(query)
        print_results(query, hits)

    print("\nRetrieval test complete.")
