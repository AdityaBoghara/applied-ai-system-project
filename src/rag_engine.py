import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction  # type: ignore[import-untyped]

_KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "data" / "knowledge_base"
_CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_store"
_COLLECTION_NAME = "genre_knowledge"

_collection: chromadb.Collection | None = None
_embed_fn = DefaultEmbeddingFunction()


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is not None:
        return _collection

    client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
    collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0:
        _ingest(collection)

    _collection = collection
    return _collection


def _ingest(collection: chromadb.Collection) -> None:
    txt_files = sorted(_KNOWLEDGE_BASE_DIR.glob("*.txt"))

    documents, ids, metadatas = [], [], []
    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        genre = txt_file.stem
        documents.append(text)
        ids.append(genre)
        metadatas.append({"genre": genre, "source": txt_file.name})

    if documents:
        collection.add(documents=documents, ids=ids, metadatas=metadatas)


def retrieve_context(song_genre: str, song_mood: str) -> str:
    """Return the most relevant knowledge chunk for a given genre and mood."""
    collection = _get_collection()
    query = f"{song_genre} music {song_mood} mood"

    results = collection.query(
        query_texts=[query],
        n_results=1,
        include=["documents"],
    )

    docs = results.get("documents", [[]])
    if docs and docs[0]:
        return docs[0][0]
    return ""
