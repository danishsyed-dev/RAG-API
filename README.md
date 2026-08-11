# RAG-API — Local Retrieval-Augmented Generation API

A lightweight, privacy-first API to query a knowledge base with natural language using local LLMs and vector search.

## Introduction & Goals

RAG-API lets you ingest plain text documents, create vector embeddings with ChromaDB, and answer natural-language queries using a local LLM (Ollama + TinyLlama) served behind a FastAPI HTTP API.

- Data: small technical and documentation files (example: `k8s.txt`) and any `.txt`/`.md` files you add and embed via `embed.py`.
- Tools: `FastAPI`, `ChromaDB` (local), `Ollama` (TinyLlama), `pytest` for tests, and optional Kubernetes manifests for deployment.
- What it does: ingests and chunks documents, stores embeddings in a local ChromaDB collection, retrieves nearest chunks for a query, and synthesizes an answer using a local LLM.

Conclusion (short): RAG-API provides a reproducible, local retrieval-augmented generation stack for private knowledge-base Q&A. It runs fully on a developer machine, reproduces embeddings deterministically from source files, and exposes a small HTTP API for queries and document management.

**Goal 1:** Provide a private local RAG API that answers KB queries.
**How I know it worked:** The `/health` endpoint returns `status: "healthy"` and `document_count >= 1`, and `pytest tests/ -q` completes successfully (exit code 0).

**Goal 2:** Reproducible ingestion and chunking pipeline.
**How I know it worked:** Running `python embed.py` creates/updates the ChromaDB files under `./db` and `tests/test_embed.py` passes.

**Goal 3:** Fast local feedback loop for development.
**How I know it worked:** Health endpoint and simple queries return within a few seconds on a typical developer laptop (empirically verifiable with `time` on your machine).

> **Why this matters:** The project prioritizes privacy and reproducibility: everything runs locally, you can reproduce embeddings and QA behavior without external services, and the tests demonstrate correctness in CI and locally.

## Architecture

View the architecture diagram: [images/architecture.svg](images/architecture.svg#L1).

Top-level flow: `embed.py` (ingest & chunk) → ChromaDB (`./db`) → `app.py` (FastAPI) → Ollama (TinyLlama) for local synthesis.

## Contents

- [The Data Set](#the-data-set)
- [Constraints](#constraints)
- [Used Tools](#used-tools)
  - [Connect](#connect)
  - [Buffer](#buffer)
  - [Processing](#processing)
  - [Storage](#storage)
  - [Visualization](#visualization)
- [Pipelines](#pipelines)
  - [Stream Processing](#stream-processing)
  - [Batch Processing](#batch-processing)
  - [Visualizations](#visualizations)
- [Demo](#demo)
- [What Breaks](#what-breaks)
- [Conclusion](#conclusion)
- [Follow Me On](#follow-me-on)
- [Appendix](#appendix)

## The Data Set

- The repository ships with small sample documents such as `k8s.txt`. The intent is to index technical documentation and small knowledge files (markdown, plain text).
- Choice: simple, human-readable docs make it easy to inspect chunks and test retrieval quality.
- Problematic: the project is not designed for high-volume streaming data or large binary blobs.
- Goal: enable reliable Q&A over a small corpus and provide a straightforward path to scale later.

### How much data is it

Concrete example from this repository:

`k8s.txt` (sample file) contains a single line: "Kubernetes is a container orchestration platform used to manage containers at scale." — 84 characters (~84 bytes). With the default `CHUNK_SIZE=500` this yields 1 chunk and therefore 1 embedding in ChromaDB.

If you add 1,000 similar small documents (≈1 KB each), you'd have ~1,000 chunks; at an estimated 4 KB per serialized embedding that's ~4 MB of vector storage — still small for a single-machine dev setup. Use sharding or an external vector host when you reach tens or hundreds of thousands of chunks.

## Constraints

- Budget: development on a laptop / free-tier resources.
- Compute: designed to run on a developer machine or a small VM; Ollama inference requires the model locally and enough RAM for TinyLlama.
- Data you do not control: none in the sample; external integrations would impose rate limits.
- Time: iterative project developed over a few days; tests and CI provide automated checks.

## Used Tools

This project picks small, local-first components so the whole stack can run without cloud services.

### Connect

No external ingestion service — documents are added via `embed.py` (batch) or the document API endpoints. See [embed.py](embed.py#L1).

Setup (one-liner):

```bash
python embed.py --file k8s.txt
```

Why: simple, file-driven ingestion keeps the pipeline reproducible and easy to debug. Rejected alternatives: webhook-based ingestion (adds operational complexity) and cloud-only ingestion (breaks local reproducibility).

### Buffer

None — at this scale a message queue wasn't necessary. For higher throughput, Kafka or Pub/Sub would be considered.

### Processing

 - Document chunking & embedding: `embed.py` (Python). See [embed.py](embed.py#L1).
 - API & orchestration: `app.py` (FastAPI) serves endpoints for health, queries, and document CRUD. See [app.py](app.py#L1).

Setup (one-liners):

```bash
# Run tests
pytest tests/ -q

# Run API (mock LLM mode for development/CI)
USE_MOCK_LLM=1 uvicorn app:app --reload
```

Why: Python + FastAPI offers fast developer feedback and easy testability. Considered alternatives: a heavier microservices approach (unnecessary at this scale) and hosted LLM APIs (rejected for privacy reasons).

### Storage

 - ChromaDB local collection stored under `./db` (sqlite + collection files). Configuration in [config.py](config.py#L1).

Setup (one-liner):

```bash
# Storage is created automatically when running `embed.py`. No manual DB init required.
python embed.py --file k8s.txt
```

Why: ChromaDB provides a lightweight, embeddable vector store suitable for single-machine workflows. Considered alternatives: FAISS (more low-level), Pinecone (hosted) — Chroma balances ease-of-use and local operation.

### Visualization

- The primary interface is the HTTP API (`/query`, `/documents`, `/health`). A simple frontend could be added, but is intentionally out of scope.

## Pipelines

High-level:

- Batch ingestion: `python embed.py --file k8s.txt` reads the file, chunks text, computes embeddings, and writes them to the ChromaDB collection. Key code: [embed.py](embed.py#L1).
- Query flow: `POST /query` in `app.py` looks up nearest neighbors in ChromaDB and formats a prompt for Ollama. Key code: [app.py](app.py#L1).

Error handling: bad documents are skipped with logging during embedding; the API returns safe errors for malformed requests. Tests exercise the main paths (`tests/`).

### Stream Processing

Not implemented — this project uses batch ingestion. For streaming, you could add a small consumer that watches a directory or a message queue and calls the embed endpoint.

### Batch Processing

Implemented via `embed.py`. The script supports file, directory, chunk-size, and overlap options.

### Visualizations

None included. The API returns JSON you can wire to any frontend or BI tool.

## Demo

- Start Ollama (if using real LLM): install and run Ollama, pull `tinyllama`.
- Seed data: `python embed.py`
- Run the app: `uvicorn app:app --reload`
- Try: `curl -X POST localhost:8000/query -H "Content-Type: application/json" -d '{"query":"What is Kubernetes?","n_results":3}'`

### Sample Query & Response (canned)

Request:

```bash
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is Kubernetes?","n_results":3}'
```

Response (example):

```json
{
  "answer": "Kubernetes is a container orchestration platform used to manage containers at scale.",
  "sources": [
    {
      "id": "k8s_chunk_0",
      "content": "Kubernetes is a container orchestration platform used to manage containers at scale.",
      "metadata": {"source": "k8s.txt", "chunk_index": 0}
    }
  ]
}
```

## What Breaks

- **What breaks first:** Large volumes of documents (100k+ chunks) will increase memory and IO pressure on ChromaDB; solution: shard collections or move to a vector-hosted solution.
- **What I skipped:** A web UI and production-grade auth. Both are omitted to keep the repo focused and small.
- **Risk accepted:** Running the LLM locally assumes you will manage model storage and RAM; if that fails, switch to a remote LLM.

If the data touches people, add a short privacy note here (not applicable to the sample docs included).

## Conclusion

RAG-API is a compact, local-first retrieval-augmented generation stack designed for experimentation and private KB question answering. The main lessons: keep chunking and metadata predictable, test embeddings and retrieval logic, and prefer small, reproducible components when privacy is a concern.

Key takeaways:
- Tests (`pytest`) are the single best way to ensure the ingestion and query behavior remain stable.
- Partitioning and metadata choices early make queries much faster to tune later.

## Follow Me On

Github : https://www.github.com/danishsyed-dev

## Appendix

- Run tests: `pytest tests/ -v`
- Embed a file: `python embed.py --file k8s.txt`
- Start server (mock LLM mode for CI): `USE_MOCK_LLM=1 uvicorn app:app --reload`

---

Files of interest: [app.py](app.py#L1), [embed.py](embed.py#L1), [config.py](config.py#L1), tests: [tests/](tests/)
