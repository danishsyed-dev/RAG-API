"""Shared pytest fixtures for the RAG-API test suite."""

import os
import shutil

import pytest

# ---------------------------------------------------------------------------
# Set test environment variables BEFORE any app imports.
# ---------------------------------------------------------------------------
os.environ["USE_MOCK_LLM"] = "1"
os.environ["CHROMADB_PATH"] = "./test_db"
os.environ["COLLECTION_NAME"] = "test_docs"

from fastapi.testclient import TestClient  # noqa: E402

from app import app, collection  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seed_test_data():
    """Seed the test database with sample documents and clean up afterwards."""
    collection.upsert(
        documents=[
            "Kubernetes is a container orchestration platform used to manage containers at scale.",
            "Docker is a containerization platform that packages applications into containers.",
            "Python is a high-level programming language known for its readability and versatility.",
        ],
        ids=["k8s_doc", "docker_doc", "python_doc"],
        metadatas=[
            {"source": "k8s.txt", "chunk_index": 0, "total_chunks": 1},
            {"source": "docker.txt", "chunk_index": 0, "total_chunks": 1},
            {"source": "python.txt", "chunk_index": 0, "total_chunks": 1},
        ],
    )
    yield
    # Cleanup
    if os.path.exists("./test_db"):
        shutil.rmtree("./test_db", ignore_errors=True)


@pytest.fixture(scope="session")
def client():
    """Provide a FastAPI ``TestClient`` for the session."""
    with TestClient(app) as c:
        yield c
