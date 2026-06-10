"""RAG-API — Retrieval-Augmented Generation API.

A lightweight API for querying a knowledge base with natural language
and getting intelligent responses powered by local LLMs.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import chromadb
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("rag-api")

# ---------------------------------------------------------------------------
# Conditional LLM import
# ---------------------------------------------------------------------------
ollama_client = None
if not settings.use_mock_llm:
    try:
        import ollama as _ollama

        ollama_client = _ollama
    except ImportError:
        logger.warning(
            "ollama package not installed — LLM features will be unavailable."
        )


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=settings.max_query_length,
        description="The question to ask the knowledge base.",
    )
    n_results: int = Field(
        default=settings.default_n_results,
        ge=1,
        le=10,
        description="Number of context chunks to retrieve.",
    )


class Source(BaseModel):
    """A single source document returned alongside the answer."""

    content: str
    id: str
    metadata: dict = {}


class QueryResponse(BaseModel):
    """Response from the /query endpoint."""

    answer: str
    sources: list[Source] = []


class AddRequest(BaseModel):
    """Request body for adding a document."""

    text: str = Field(
        ..., min_length=1, description="Text content to add to the knowledge base."
    )
    id: Optional[str] = Field(
        default=None, description="Optional document ID (auto-generated if omitted)."
    )
    metadata: dict = Field(
        default_factory=dict, description="Optional metadata for the document."
    )


class AddResponse(BaseModel):
    """Response from the document-add endpoint."""

    message: str
    id: str


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str
    database: str
    llm: str
    document_count: int


class DocumentListResponse(BaseModel):
    """Response from listing documents."""

    documents: list[Source]
    total: int


# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RAG-API …")
    logger.info("  ChromaDB path : %s", settings.chromadb_path)
    logger.info("  LLM model     : %s", settings.llm_model)
    logger.info("  Mock LLM      : %s", settings.use_mock_llm)
    yield
    logger.info("Shutting down RAG-API …")


app = FastAPI(
    title="RAG-API",
    description="Retrieval-Augmented Generation API powered by ChromaDB & Ollama.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chroma = chromadb.PersistentClient(path=settings.chromadb_path)
collection = chroma.get_or_create_collection(settings.collection_name)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check the health of the API, database, and LLM connectivity."""
    db_status = "healthy"
    llm_status = "mock" if settings.use_mock_llm else "unknown"
    doc_count = 0

    try:
        doc_count = collection.count()
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_status = "unhealthy"

    if not settings.use_mock_llm and ollama_client is not None:
        try:
            ollama_client.list()
            llm_status = "healthy"
        except Exception as exc:
            logger.error("LLM health check failed: %s", exc)
            llm_status = "unhealthy"

    overall = (
        "healthy"
        if db_status == "healthy" and llm_status in ("healthy", "mock")
        else "degraded"
    )
    return HealthResponse(
        status=overall,
        database=db_status,
        llm=llm_status,
        document_count=doc_count,
    )


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """Query the knowledge base and get an AI-generated answer."""
    try:
        count = collection.count()
        if count == 0:
            raise HTTPException(
                status_code=404,
                detail="Knowledge base is empty. Add documents first.",
            )
        results = collection.query(
            query_texts=[request.query],
            n_results=min(request.n_results, count),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        raise HTTPException(
            status_code=500, detail="Failed to query the knowledge base."
        )

    documents = results.get("documents", [[]])[0]
    ids = results.get("ids", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if not documents:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    sources = [
        Source(content=doc, id=doc_id, metadata=meta or {})
        for doc, doc_id, meta in zip(documents, ids, metadatas)
    ]
    context = "\n\n---\n\n".join(documents)

    # In mock mode, return the raw context directly
    if settings.use_mock_llm:
        return QueryResponse(answer=context, sources=sources)

    if ollama_client is None:
        raise HTTPException(
            status_code=503,
            detail="LLM service is not configured. Install the ollama package.",
        )

    try:
        response = ollama_client.generate(
            model=settings.llm_model,
            prompt=(
                "You are a helpful assistant. Answer the question based ONLY on "
                "the provided context. If the context doesn't contain enough "
                "information, say so.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {request.query}\n\n"
                "Answer clearly and concisely:"
            ),
        )
    except Exception as exc:
        logger.error("Ollama generation failed: %s", exc)
        raise HTTPException(status_code=503, detail="LLM service is unavailable.")

    return QueryResponse(answer=response["response"], sources=sources)


@app.post("/documents", response_model=AddResponse)
def add_document(request: AddRequest):
    """Add a new document to the knowledge base."""
    doc_id = request.id or str(uuid.uuid4())
    metadata = request.metadata if request.metadata else {"source": "api"}

    try:
        collection.upsert(
            documents=[request.text],
            ids=[doc_id],
            metadatas=[metadata],
        )
    except Exception as exc:
        logger.error("Failed to add document: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to add document to the knowledge base.",
        )

    logger.info("Document added: %s", doc_id)
    return AddResponse(message="Document added successfully.", id=doc_id)


@app.get("/documents", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List documents in the knowledge base with pagination."""
    try:
        total = collection.count()
        if total == 0:
            return DocumentListResponse(documents=[], total=0)

        results = collection.get(limit=limit, offset=offset)
        documents = [
            Source(content=doc, id=doc_id, metadata=meta or {})
            for doc, doc_id, meta in zip(
                results.get("documents", []),
                results.get("ids", []),
                results.get("metadatas", []),
            )
        ]
        return DocumentListResponse(documents=documents, total=total)
    except Exception as exc:
        logger.error("Failed to list documents: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list documents.")


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Delete a document from the knowledge base by ID."""
    try:
        collection.delete(ids=[doc_id])
    except Exception as exc:
        logger.error("Failed to delete document %s: %s", doc_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete document.")

    logger.info("Document deleted: %s", doc_id)
    return {"message": f"Document '{doc_id}' deleted successfully."}
