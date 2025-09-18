\
import os, pickle, yaml
from typing import List, Dict, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder

def load_artifacts(index_dir: str, emb_model_name: str):
    index = faiss.read_index(os.path.join(index_dir, "faiss.index"))
    chunks = pickle.load(open(os.path.join(index_dir, "chunks.pkl"), "rb"))
    bm25 = pickle.load(open(os.path.join(index_dir, "bm25.pkl"), "rb"))
    st = SentenceTransformer(emb_model_name)
    return index, chunks, bm25, st

def dense_search(index, st, query: str, chunks: List[Dict], top_k: int) -> List[Tuple[int, float]]:
    q = st.encode([query], normalize_embeddings=True)
    D, I = index.search(q.astype(np.float32), top_k)
    return [(int(idx), float(score)) for idx, score in zip(I[0], D[0])]

def bm25_search(bm25, query: str, top_k: int) -> List[Tuple[int, float]]:
    scores = bm25.get_scores(query.split())
    idx = np.argsort(scores)[::-1][:top_k]
    return [(int(i), float(scores[i])) for i in idx]

def rrf_fusion(dense_hits, bm25_hits, k=60) -> Dict[int, float]:
    # Convert to ranks then fuse
    ranks_dense = {idx: r+1 for r,(idx,_) in enumerate(sorted(dense_hits, key=lambda x: -x[1]))}
    ranks_bm25 = {idx: r+1 for r,(idx,_) in enumerate(sorted(bm25_hits, key=lambda x: -x[1]))}
    fused = {}
    for idx, r in ranks_dense.items():
        fused[idx] = fused.get(idx, 0.0) + 1.0/(k + r)
    for idx, r in ranks_bm25.items():
        fused[idx] = fused.get(idx, 0.0) + 1.0/(k + r)
    return fused

def weighted_fusion(dense_hits, bm25_hits, alpha_dense=0.6, alpha_bm25=0.4) -> Dict[int, float]:
    scores = {}
    for idx, s in dense_hits:
        scores[idx] = scores.get(idx, 0.0) + alpha_dense * s
    for idx, s in bm25_hits:
        scores[idx] = scores.get(idx, 0.0) + alpha_bm25 * s
    return scores

def cross_encode_rerank(candidates: List[int], query: str, chunks: List[Dict], ce_model_name: str, top_k: int):
    ce = CrossEncoder(ce_model_name)
    pairs = [(query, chunks[i]["text"]) for i in candidates]
    scores = ce.predict(pairs)
    order = np.argsort(scores)[::-1][:top_k]
    return [candidates[i] for i in order]

def retrieve(query: str, cfg) -> List[Dict]:
    index_dir = cfg["paths"]["index_dir"]
    emb_model = cfg["embeddings_model"]
    index, chunks, bm25, st = load_artifacts(index_dir, emb_model)

    k_dense = cfg["retrieval"]["top_k_dense"]
    k_bm25 = cfg["retrieval"]["top_k_bm25"]
    fusion = cfg["retrieval"]["fusion"]

    dense_hits = dense_search(index, st, query, chunks, k_dense)
    bm25_hits = bm25_search(bm25, query, k_bm25)

    if fusion == "rrf":
        fused = rrf_fusion(dense_hits, bm25_hits, k=60)
    else:
        fused = weighted_fusion(dense_hits, bm25_hits, cfg["retrieval"]["alpha_dense"], cfg["retrieval"]["alpha_bm25"])

    # Top candidates by fused score
    top_ids = [idx for idx,_ in sorted(fused.items(), key=lambda x: -x[1])]
    # Optional cross-encoder rerank
    if cfg["retrieval"].get("use_cross_encoder_rerank", False) and len(top_ids)>0:
        top_ids = cross_encode_rerank(top_ids, query, chunks, cfg["retrieval"]["cross_encoder_model"], cfg["retrieval"]["rerank_top_k"])
    return [chunks[i] for i in top_ids]
