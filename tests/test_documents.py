"""Tests for document CRUD endpoints."""


def test_add_document_with_id(client):
    """Adding a document with an explicit ID should succeed."""
    response = client.post(
        "/documents",
        json={
            "text": "FastAPI is a modern web framework for Python.",
            "id": "test_fastapi",
            "metadata": {"source": "test"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_fastapi"
    assert "success" in data["message"].lower()


def test_add_document_auto_id(client):
    """Adding a document without an ID should auto-generate one."""
    response = client.post(
        "/documents", json={"text": "This is a test document."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"]  # Non-empty auto-generated UUID


def test_add_empty_document_rejected(client):
    """Empty document text should fail validation."""
    response = client.post("/documents", json={"text": ""})
    assert response.status_code == 422


def test_list_documents(client):
    """Listing documents should return a valid response."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert data["total"] >= 3  # At least our seeded docs


def test_list_documents_pagination(client):
    """Pagination parameters should limit results."""
    response = client.get("/documents?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) <= 2


def test_delete_document(client):
    """Deleting a document should succeed."""
    # First add a document
    client.post(
        "/documents",
        json={"text": "Temporary document for deletion test.", "id": "delete_me"},
    )
    # Then delete it
    response = client.delete("/documents/delete_me")
    assert response.status_code == 200
    assert "delete_me" in response.json()["message"]


def test_upsert_duplicate_id(client):
    """Upserting a document with the same ID should update, not crash."""
    payload = {"text": "Version 1 of the doc.", "id": "upsert_test"}
    client.post("/documents", json=payload)

    payload["text"] = "Version 2 of the doc."
    response = client.post("/documents", json=payload)
    assert response.status_code == 200
