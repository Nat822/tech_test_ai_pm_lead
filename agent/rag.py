"""
RAG pipeline — document loading, chunking, ChromaDB indexing and retrieval.
"""
from __future__ import annotations

import logging
from pathlib import Path

import chromadb

from agent.llm import nd_embed

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths and collection name
# ---------------------------------------------------------------------------

_BASE_DIR = Path(__file__).parent
DATA_DIR = _BASE_DIR / "data"
EMBED_DIR = _BASE_DIR / "embeddings"
COLLECTION_NAME = "project_docs"

# ---------------------------------------------------------------------------
# ChromaDB persistent client (module-level singleton)
# ---------------------------------------------------------------------------

_chroma = chromadb.PersistentClient(path=str(EMBED_DIR))


def _get_collection() -> chromadb.Collection:
    return _chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def _load_documents(data_dir: Path = DATA_DIR) -> list[dict]:
    """
    Load all .txt and .md files from *data_dir*.
    Returns a list of {"source": filename, "text": content} dicts.
    """
    docs: list[dict] = []
    for path in sorted(data_dir.glob("**/*")):
        if path.suffix in (".txt", ".md") and path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
                docs.append({"source": path.name, "text": text})
                logger.debug("Loaded document: %s (%d chars)", path.name, len(text))
            except Exception as exc:
                logger.warning("Could not read %s: %s", path, exc)
    return docs


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def _chunk_text(text: str, size: int = 400, overlap: int = 60) -> list[str]:
    """
    Split *text* into overlapping chunks of approximately *size* characters.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if c]  # drop empty chunks


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

async def index_documents(data_dir: Path = DATA_DIR) -> int:
    """
    Load, chunk, embed and upsert all documents into ChromaDB.
    Deletes the existing collection first to guarantee no stale chunks remain.
    Returns the total number of chunks indexed.
    """
    docs = _load_documents(data_dir)
    if not docs:
        logger.warning("No .txt/.md documents found in %s", data_dir)
        return 0

    # Delete collection to remove any stale (e.g. previously English) chunks
    try:
        _chroma.delete_collection(COLLECTION_NAME)
        logger.info("Deleted existing collection '%s' before re-indexing.", COLLECTION_NAME)
    except Exception:
        pass  # collection may not exist yet on first run

    collection = _get_collection()

    all_chunks: list[str] = []
    all_ids: list[str] = []
    all_metas: list[dict] = []

    for doc in docs:
        chunks = _chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['source']}::chunk_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metas.append({"source": doc["source"], "chunk_index": i})

    if not all_chunks:
        logger.warning("Documents found but produced zero chunks.")
        return 0

    # Embed in batches of 20 to avoid oversized API requests
    BATCH = 20
    all_embeddings: list[list[float]] = []
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i : i + BATCH]
        logger.debug("Embedding batch %d/%d ...", i // BATCH + 1, -(-len(all_chunks) // BATCH))
        embeddings = await nd_embed(batch)
        all_embeddings.extend(embeddings)

    collection.add(
        documents=all_chunks,
        embeddings=all_embeddings,
        ids=all_ids,
        metadatas=all_metas,
    )

    logger.info(
        "Indexed %d chunks from %d document(s) into collection '%s'.",
        len(all_chunks),
        len(docs),
        COLLECTION_NAME,
    )
    return len(all_chunks)



# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

async def retrieve(query: str, k: int = 3) -> str:
    """
    Embed *query*, search ChromaDB, and return a formatted context string.
    """
    collection = _get_collection()
    total = collection.count()

    if total == 0:
        return "База знаний пуста. Пожалуйста, сначала проиндексируйте документы."

    k = min(k, total)
    query_embedding = await nd_embed([query])

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
    )

    docs_list: list[list[str]] = results.get("documents") or [[]]
    metas_list: list[list[dict]] = results.get("metadatas") or [[{}]]

    if not docs_list[0]:
        return "Релевантный контекст не найден."

    parts: list[str] = []
    for chunk, meta in zip(docs_list[0], metas_list[0]):
        source = meta.get("source", "unknown")
        parts.append(f"[Source: {source}]\n{chunk}")

    return "\n\n---\n\n".join(parts)
