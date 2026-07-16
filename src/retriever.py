"""
Top-k semantic search against a FAISS index built by indexer.py.
"""

from src.indexer import get_embedding_model


def retrieve(query, index, chunks, k=3):
    """
    Returns the top-k most similar chunks to `query`.
    Lower "score" (L2 distance) = more similar.
    """
    model = get_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding.astype('float32'), k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        results.append({"score": float(dist), "chunk": chunks[idx]})

    return results