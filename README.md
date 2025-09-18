# SwimForge 🏊‍♂️ — Local-First Competitive Swimming Chatbot

A customized chatbot for competitive swimmers — built to **generate swimming and dryland workouts**, **analyze training performance**, and provide **expert advice on injuries and recovery**. 100% local & free (no paid APIs).

## 🌊 Features
- **Swim Workout Generator**: structured plans (free/fly/back/breast/IM) for easy → sprint goals.
- **Dryland Workout Generator**: strength, core, mobility plans.
- **Pace & Workout Analysis**: evaluate lap times, heart rates, and rest intervals.
- **Injury Advice**: common injury tips and return-to-training considerations.
- **Nutrition Advice**: structured plans (Veg / Vegan / Non‑Veg).
- **General Knowledge (RAG)**: hybrid retrieval (BM25 + FAISS) over your local docs.

## 📦 Tech (all local/free)
- Dense retrieval: FAISS + `sentence-transformers/all-MiniLM-L6-v2`
- Sparse retrieval: `rank-bm25`
- (Optional) Reranking: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Local LLM (optional): GPT4All or Ollama — or run with no LLM (context only)
- No LangChain dependency

## 🧰 Repo Layout
```
.
├── app.py                 # CLI chatbot (uses router + retrievers + local LLM or context)
├── build_index.py         # chunks & builds FAISS/BM25 locally
├── retrievers.py          # hybrid retrieval + (optional) cross-encoder re-rank
├── router.py              # intent router → workouts/analysis/advice or RAG
├── llm_backends.py        # GPT4All/Ollama/none
├── services/              # workouts/analysis/advice modules
├── docs/                  # your knowledge base (txt/md/csv/json)
├── index/                 # generated indices (gitignored)
├── data/                  # CSV templates (profiles, workouts, races, wellness)
├── prompts.yaml           # editable system/user templates
├── config.yaml            # chunking, retrieval, models, LLM backend
├── requirements.txt
├── run.sh
├── Makefile
├── Dockerfile
├── .gitignore
└── LICENSE
```

## 🚀 Quickstart (Local)
```bash
# 1) create env & install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) add your docs
# Put .txt/.md/.csv/.json into ./docs (technique, workouts, records, injury, nutrition, etc.)

# 3) build index
python build_index.py

# 4) run chatbot (CLI)
python app.py
```

### Example queries
- `generate swim workout 4000m threshold free`
- `dryland core 30`
- `analyze pace laps=[85,86,86,87] rest=[20,20,25] hr=[160,165,168]`
- `injury shoulder`
- `nutrition vegan`

## 🧪 Config & Prompts
- **Prompts**: edit `prompts.yaml` for style & rules.
- **Retriever**: tune `config.yaml → retrieval` (RRF/weighted, top‑k, reranker).
- **Chunking**: `config.yaml → chunk.size/overlap`.
- **LLM backend**: `gpt4all` (set a `.gguf` name), `ollama` (e.g., `phi3`), or `none`.

## 🐳 Run with Docker
```bash
docker build -t swimforge .
docker run --rm -it -v $PWD/docs:/app/docs swimforge
```

## 🧾 GitHub — how to push
```bash
git init
git add .
git commit -m "Initial commit: SwimForge local-first swimming chatbot"
git branch -M main
git remote add origin https://github.com/<your-username>/swim-forge.git
git push -u origin main
```

## 📄 License
MIT — do whatever, just keep the notice.
