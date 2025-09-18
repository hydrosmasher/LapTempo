\
import os
import re
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np
from tqdm import tqdm
import yaml

from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss
from rank_bm25 import BM25Okapi

# Simple text loader for .txt, .md, .csv, .json. Extend as needed (e.g., PDF via pypdf).
def load_documents(docs_dir: str) -> List[Dict]:
    docs = []
    for root, _, files in os.walk(docs_dir):
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() in [".txt", ".md"]:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                docs.append({"path": str(p), "text": txt})
            elif p.suffix.lower() == ".csv":
                # Load csv as plain text lines (user can paste structured info too)
                txt = p.read_text(encoding="utf-8", errors="ignore")
                docs.append({"path": str(p), "text": txt})
            elif p.suffix.lower() == ".json":
                try:
                    obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
                    txt = json.dumps(obj, indent=2)
                    docs.append({"path": str(p), "text": txt})
                except Exception:
                    pass
    return docs

def chunk_text(text: str, size: int, overlap: int) -> List[Tuple[str, Tuple[int,int]]]:
    # naive splitter on paragraphs with sliding window
    paras = re.split(r"\n\s*\n", text)
    chunks = []
    buf = ""
    char_count = 0
    start_char = 0
    for para in paras:
        if buf:
            buf += "\n\n" + para
        else:
            buf = para
            start_char = char_count
        char_count += len(para) + 2
        if len(buf) >= size:
            end_char = start_char + len(buf)
            chunks.append((buf, (start_char, end_char)))
            # overlap
            buf = buf[-overlap:]
            start_char = end_char - len(buf)
    if buf.strip():
        end_char = start_char + len(buf)
        chunks.append((buf, (start_char, end_char)))
    return chunks

def reciprocal_rank_fusion(ranks_dense: Dict[int,int], ranks_bm25: Dict[int,int], k=60) -> Dict[int, float]:
    scores = {}
    for idx, r in ranks_dense.items():
        scores[idx] = scores.get(idx, 0.0) + 1.0/(k + r)
    for idx, r in ranks_bm25.items():
        scores[idx] = scores.get(idx, 0.0) + 1.0/(k + r)
    return scores

def main():
    cfg = yaml.safe_load(open("config.yaml"))
    docs_dir = cfg["paths"]["docs_dir"]
    index_dir = cfg["paths"]["index_dir"]
    os.makedirs(index_dir, exist_ok=True)

    em_model_name = cfg["embeddings_model"]
    chunk_size = int(cfg["chunk"]["size"])
    chunk_overlap = int(cfg["chunk"]["overlap"])

    print(f"Loading docs from: {docs_dir}")
    raw_docs = load_documents(docs_dir)
    if not raw_docs:
        print("No documents found. Put .txt/.md/.csv/.json into ./docs and rerun.")
        return

    print(f"Chunking with size={chunk_size}, overlap={chunk_overlap}")
    all_chunks = []
    for d in raw_docs:
        chunks = chunk_text(d["text"], chunk_size, chunk_overlap)
        for c, span in chunks:
            all_chunks.append({"path": d["path"], "text": c, "span": span})

    print(f"Total chunks: {len(all_chunks)}")
    print("Building embeddings...")
    st = SentenceTransformer(em_model_name)
    embs = st.encode([c["text"] for c in all_chunks], batch_size=64, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

    # FAISS index
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embs.astype(np.float32))

    print("Building BM25...")
    tokenized = [c["text"].split() for c in all_chunks]
    bm25 = BM25Okapi(tokenized)

    # Persist
    print("Saving artifacts...")
    faiss.write_index(index, os.path.join(index_dir, "faiss.index"))
    with open(os.path.join(index_dir, "chunks.pkl"), "wb") as f:
        pickle.dump(all_chunks, f)
    with open(os.path.join(index_dir, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)
    with open(os.path.join(index_dir, "embeddings.npy"), "wb") as f:
        np.save(f, embs)

    print("Done. ✅")

if __name__ == "__main__":
    main()
