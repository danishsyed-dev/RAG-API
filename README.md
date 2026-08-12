# RAG-API — Local Retrieval-Augmented Generation API

A lightweight, privacy-first API to query a knowledge base with natural language using local LLMs and vector search.

## Introduction & Goals

RAG-API is a local, privacy-first retrieval-augmented generation service. It indexes plain text files and richer office/PDF documents, stores embeddings in ChromaDB, and answers questions through a FastAPI API backed by Ollama or a mock mode for CI.

- Ingestion: `embed.py` now accepts `.txt`, `.md`, and AnyDoc-supported formats such as Word, PowerPoint, Excel, OpenDocument, RTF, EPUB, CSV, and text-based PDF files.
- Processing: supported rich documents are converted to clean Markdown with AnyDoc before chunking, so the retrieval layer sees a single normalized text format.
- Serving: `app.py` exposes `/health`, `/query`, and `/documents` endpoints for health checks, semantic search, and CRUD operations.

Conclusion: the current project is a self-contained local RAG stack for document Q&A. It stays offline for ingestion and retrieval, and it can run in a mock LLM mode when Ollama is unavailable.

## Current Scope

- Local API: FastAPI + Pydantic request validation.
- Local storage: ChromaDB collections under `./db` or `./test_db`.
- Local inference: Ollama with TinyLlama, or `USE_MOCK_LLM=1` for tests.
- Local document conversion: AnyDoc normalizes richer documents to Markdown before embedding.

**Goal 1:** Provide a private local RAG API that answers KB queries.
**How I know it worked:** The `/health` endpoint returns `status: "healthy"` and `document_count >= 1`, and `pytest tests/ -q` completes successfully (exit code 0).

**Goal 2:** Reproducible ingestion and chunking pipeline.
**How I know it worked:** Running `python embed.py` creates/updates the ChromaDB files under `./db` and `tests/test_embed.py` passes.

**Goal 3:** Fast local feedback loop for development.
**How I know it worked:** Health endpoint and simple queries return within a few seconds on a typical developer laptop (empirically verifiable with `time` on your machine).

> **Why this matters:** The project prioritizes privacy and reproducibility: everything runs locally, you can reproduce embeddings and QA behavior without external services, and the tests demonstrate correctness in CI and locally.

## Architecture

View the architecture diagram: [images/architecture.svg](images/architecture.svg#L1).

Top-level flow: `embed.py` (convert, ingest, and chunk) → ChromaDB (`./db`) → `app.py` (FastAPI) → Ollama (TinyLlama) for local synthesis.

## Contents

- [Current Scope](#current-scope)
- [Supported Formats](#supported-formats)
- [Setup](#setup)
- [Usage](#usage)
- [API](#api)
- [Tests](#tests)
- [Notes](#notes)

## Supported Formats

- Plain text: `.txt`, `.md`.
- AnyDoc conversions: `.doc`, `.docx`, `.docm`, `.ppt`, `.pptx`, `.pptm`, `.pps`, `.ppsx`, `.ppsm`, `.pot`, `.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.odt`, `.ods`, `.odp`, `.rtf`, `.epub`, `.csv`, `.pdf`.
- The ingestion pipeline converts rich formats to Markdown first, then chunks the normalized text for embedding.

### How much data is it

Concrete example from this repository:

`k8s.txt` (sample file) contains a single line: "Kubernetes is a container orchestration platform used to manage containers at scale." — 84 characters (~84 bytes). With the default `CHUNK_SIZE=500` this yields 1 chunk and therefore 1 embedding in ChromaDB.

If you add 1,000 similar small documents (≈1 KB each), you'd have ~1,000 chunks; at an estimated 4 KB per serialized embedding that's ~4 MB of vector storage — still small for a single-machine dev setup. Use sharding or an external vector host when you reach tens or hundreds of thousands of chunks.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Ingest the default sample document
python embed.py

# Ingest a single file or a directory
python embed.py --file path/to/report.docx
python embed.py --dir path/to/documents

# Run the API in mock mode for local development
USE_MOCK_LLM=1 uvicorn app:app --reload
```

## API

- `GET /health` checks ChromaDB and Ollama connectivity.
- `POST /query` retrieves top-k context chunks and returns either a mock response or an Ollama-generated answer.
- `POST /documents` adds a document chunk directly.
- `GET /documents` lists indexed documents with pagination.
- `DELETE /documents/{doc_id}` removes a document by ID.

## Tests

```bash
python -m pytest tests -q
```

## Notes

- `USE_MOCK_LLM=1` keeps the API usable when Ollama is not running.
- The current ingestion model is batch-based; documents are normalized locally before vectorization.

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
