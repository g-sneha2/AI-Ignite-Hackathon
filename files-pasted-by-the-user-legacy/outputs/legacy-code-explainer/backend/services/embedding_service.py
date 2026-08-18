import os, re
import numpy as np
from .cache_service import get_cached, set_cached

def chunk_files(files: dict[str,str], size=2800) -> list[dict]:
    chunks=[]
    for path, text in files.items():
        for i in range(0, len(text), size): chunks.append({"file_path":path, "text":text[i:i+size]})
    return chunks

def _fallback_vector(text: str, dims=256):
    v=np.zeros(dims, dtype=float)
    for word in re.findall(r"\w+", text.lower()): v[hash(word)%dims] += 1
    norm=np.linalg.norm(v); return (v/norm).tolist() if norm else v.tolist()

def build_index(repo_id: str, files: dict[str,str]) -> dict:
    cached=get_cached(repo_id,"embeddings","index")
    if cached: return cached
    chunks=chunk_files(files)
    api_key=os.getenv("COHERE_API_KEY")
    if api_key and chunks:
        try:
            import cohere
            client=cohere.ClientV2(api_key)
            response=client.embed(texts=[c["text"] for c in chunks], model="embed-v4.0", input_type="search_document")
            for c,e in zip(chunks,response.embeddings.float): c["embedding"]=e
        except Exception:
            for c in chunks: c["embedding"]=_fallback_vector(c["text"])
    else:
        for c in chunks: c["embedding"]=_fallback_vector(c["text"])
    return set_cached(repo_id,"embeddings","index",{"chunks":chunks})

def search(index: dict, question: str, k=5):
    # If there's no index or no chunks, return empty
    if not index or not index.get("chunks"):
        return []

    # Try to produce a query embedding using the same model as the index (Cohere) when possible
    q = None
    api_key = os.getenv("COHERE_API_KEY")
    if api_key:
        try:
            import cohere
            client = cohere.ClientV2(api_key)
            resp = client.embed(texts=[question], model="embed-v4.0", input_type="search_query")
            q = np.array(resp.embeddings.float[0])
        except Exception:
            q = None

    scored = []
    for c in index["chunks"]:
        v = np.array(c.get("embedding") or [])

        # If we couldn't get a Cohere query embedding, or v is present but dims differ,
        # fall back to a hashed vector sized to match the stored embedding when possible.
        if q is None:
            dims = v.size if v.size else 256
            q = np.array(_fallback_vector(question, dims=dims))

        # If sizes differ, align by truncating or padding the smaller vector with zeros.
        if q.size != v.size:
            if v.size == 0:
                v = np.array(_fallback_vector(c.get("text", ""), dims=q.size))
            elif q.size > v.size:
                v = np.pad(v, (0, q.size - v.size))
            else:
                v = v[: q.size]

        denom = (np.linalg.norm(q) * np.linalg.norm(v)) or 1
        score = float(np.dot(q, v) / denom)
        scored.append((score, c))

    return [c for _, c in sorted(scored, key=lambda x: x[0], reverse=True)[:k]]
