# InsightAI

A cross-domain reasoning and strategy engine built on top of the [Endee](https://github.com/EndeeLabs/endee) vector database. Upload any PDF or text document and ask questions — InsightAI goes beyond simple retrieval to produce structured, intent-aware reasoning output.

---

## What it does

Most document Q&A tools find relevant text and return it verbatim. InsightAI adds a reasoning layer on top:

- Detects **what you're asking** (WHY / STRATEGY / IMPROVE / SUMMARY)
- Detects **what domain** the document belongs to (academic / sports / resume / general)
- Retrieves the most relevant chunks from Endee via semantic search
- Passes them through a structured reasoning engine powered by **Llama 3.3 70B** (via OpenRouter)
- Returns a fully structured output — analysis, key issues, root causes, strategy, improvement plan, sources

---

## Architecture

```
PDF / TXT Upload
      │
      ▼
pdf_loader.py        — extract text page by page
      │
      ▼
chunker.py           — split into 300–500 word chunks with overlap
      │
      ▼
embedder.py          — generate 384-dim embeddings (all-MiniLM-L6-v2)
      │
      ▼
endee_client.py      — upsert vectors + metadata into Endee via REST API
      │
      ▼
  ┌─────────────────────────────────┐
  │     ENDEE VECTOR DATABASE       │
  │   HNSW index · cosine space     │
  └─────────────────────────────────┘
      │
      ▼  (at query time)
router.py            — intent detection + domain detection + query transformation
      │
      ▼
retriever.py         — embed query → Endee similarity search → top-K chunks
      │
      ▼
analyzer.py          — extract observations, issues, numeric findings, positives
      │
      ▼
reasoning_engine.py  — route to: root_cause / strategy / improvement / summary
      │
      ▼
planner.py           — generate prioritised, domain-specific action plans
      │
      ▼
Structured Output    — Analysis · Key Issues · Root Causes · Strategy · Plan · Sources
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Vector database | [Endee](https://github.com/EndeeLabs/endee) (HNSW, cosine, float32) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) |
| LLM | Llama 3.3 70B Instruct via [OpenRouter](https://openrouter.ai) (free tier) |
| LLM fallback | Gemma 3 12B via OpenRouter |
| UI | Streamlit |
| PDF parsing | PyPDF2 |
| Search response | MessagePack (decoded by `msgpack`) |

---

## Project Structure

```
insight-ai/
├── app.py                  — core InsightAI pipeline class
├── requirements.txt
├── .env                    — API keys and config (not committed)
├── data/                   — place sample documents here
├── ui/
│   └── streamlit_app.py    — Streamlit web interface
└── utils/
    ├── pdf_loader.py       — PDF and plain text extraction
    ├── chunker.py          — token-aware chunking (300–500 words, with overlap)
    ├── embedder.py         — sentence-transformer embeddings
    ├── endee_client.py     — Endee HTTP client (index, upsert, search, filter)
    ├── retriever.py        — query embedding + Endee search + re-ranking
    ├── router.py           — intent & domain detection, query transformation
    ├── analyzer.py         — pattern extraction from retrieved context
    ├── reasoning_engine.py — LLM-powered structured reasoning
    └── planner.py          — domain-specific improvement plan generation
```

---

## Prerequisites

- Python 3.10+
- Docker (to run Endee)
- An [OpenRouter](https://openrouter.ai) API key (free account works)

---

## Setup

### 1. Start Endee

Build from source (already done if you cloned this repo):

```bash
cd endee
docker compose up -d
```

Verify it's healthy:

```bash
curl http://localhost:8080/api/v1/health
# {"status":"ok"}
```

Endee runs on port **8080** by default.

---

### 2. Configure environment

Create or edit `insight-ai/.env`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
ENDEE_HOST=http://localhost:8080
ENDEE_INDEX=insightai_docs
```

Get a free OpenRouter API key at https://openrouter.ai/keys

---

### 3. Install Python dependencies

```bash
cd insight-ai
pip install -r requirements.txt
```

> On first run, `sentence-transformers` will download the `all-MiniLM-L6-v2` model (~90 MB). It is cached locally after that.

---

### 4. Launch the UI

```bash
cd insight-ai
streamlit run ui/streamlit_app.py
```

Open **http://localhost:8501** in your browser.

---

## How to use

1. **Upload** — drag a PDF or text file into the upload area and click **Load**
   - The index is cleared automatically on each new load, so previous documents don't pollute results
2. **Ask** — type a question or click one of the example chips
3. **Read** — the output is structured into sections based on your intent

Each new Load wipes the previous data and ingests only the current document(s).

---

## Intent routing

InsightAI detects what you're asking and routes to the appropriate reasoning mode:

| Intent | Triggered by | Output sections |
|---|---|---|
| **WHY** | "why", "reason", "cause", "explain" | Analysis, Key Issues, Root Causes, Contributing Factors, Strategy Insight, Improvement Plan |
| **STRATEGY** | "strategy", "plan", "approach", "how should" | Analysis, Key Issues, Strategic Pillars, Tactical Steps, Strategy Insight, Improvement Plan |
| **IMPROVE** | "improve", "better", "enhance", "increase" | Analysis, Key Issues, Strategy Insight, Improvement Plan, Short-Term Goals, Long-Term Strategy, Success Metrics, Priority Areas |
| **SUMMARY** | "summarise", "what is", "overview", "tell me" | Analysis, Key Issues, Highlights, Strategy Insight, Improvement Plan |

---

## Domain detection

| Domain | Detected from |
|---|---|
| **academic** | marks, grades, subjects, scores, exam, student |
| **sports** | match, team, player, performance, training, coach |
| **resume** | experience, skills, job, career, qualification, work |
| **general** | everything else |

---

## Endee integration

InsightAI uses Endee exclusively — no FAISS, Chroma, Pinecone, or any other vector store.

### API endpoints used

| Operation | Endpoint |
|---|---|
| Create index | `POST /api/v1/index/create` |
| Insert vectors | `POST /api/v1/index/{name}/vector/insert` |
| Similarity search | `POST /api/v1/index/{name}/search` |
| List indexes | `GET /api/v1/index/list` |
| Delete index | `DELETE /api/v1/index/{name}/delete` |
| Health check | `GET /api/v1/health` |

### Vector storage format

Each document chunk is stored as:

```json
{
  "id":     "report.pdf_p3_c1",
  "vector": [0.12, -0.04, "...384 floats..."],
  "meta":   "{\"text\": \"...\", \"page\": 3, \"chunk_index\": 1, \"doc_name\": \"report.pdf\", \"word_count\": 412}",
  "filter": "{\"doc_name\": \"report.pdf\", \"page\": 3}"
}
```

### Filtering

Queries are filtered by `doc_name` using Endee's category filter:

```json
[{"doc_name": {"$eq": "report.pdf"}}]
```

This ensures results come only from the currently loaded document.

### Search response

Endee returns search results as MessagePack with layout:

```
[rank, id, meta_bytes, filter_str, cosine_distance, vector]
```

Cosine distance is converted to similarity score: `score = 1.0 - distance`

---

## Example queries

| Query | Intent | Domain |
|---|---|---|
| "Why did I score less in mathematics?" | WHY | academic |
| "What strategy should I follow to improve my grades?" | STRATEGY | academic |
| "How can I improve my overall performance?" | IMPROVE | general |
| "Summarise my academic report" | SUMMARY | academic |
| "Why did the team lose the match?" | WHY | sports |
| "How can I strengthen my resume?" | IMPROVE | resume |

---

## Advanced options

Click **Advanced options** in the UI to access:

- **Filter by document** — restrict retrieval to a specific uploaded document (auto-set when one doc is loaded)
- **Chunks to retrieve** — control how many context chunks are fetched from Endee (3–20, default 10)
- **Show context chunks** — display the raw retrieved chunks alongside the answer

---

## Troubleshooting

**"No context available" after asking a question**
- Make sure you clicked **Load** after uploading the file, not just selected it
- Check that Endee is running: `curl http://localhost:8080/api/v1/health`

**Getting answers from a different document**
- Click **Load** again with your current file — this clears the index and re-ingests only the new document

**LLM not responding / generic answers**
- Check your `OPENROUTER_API_KEY` in `.env`
- The free tier has rate limits — wait a moment and retry
- The fallback model (Gemma 3 12B) activates automatically if Llama 3.3 70B is unavailable

**Streamlit app not starting**
- Ensure you're running from the `insight-ai/` directory
- Check all dependencies are installed: `pip install -r requirements.txt`

---

## License

InsightAI is built on top of [Endee](https://github.com/EndeeLabs/endee).  
See `endee/LICENSE` for the Endee license.
