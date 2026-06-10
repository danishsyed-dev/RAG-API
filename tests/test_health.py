"""Tests for the GET /health endpoint."""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape(client):
    data = client.get("/health").json()
    assert "status" in data
    assert "database" in data
    assert "llm" in data
    assert "document_count" in data


def test_health_database_healthy(client):
    data = client.get("/health").json()
    assert data["database"] == "healthy"


def test_health_mock_llm(client):
    data = client.get("/health").json()
    assert data["llm"] == "mock"


def test_health_document_count(client):
    data = client.get("/health").json()
    assert data["document_count"] >= 3  # We seeded 3 documents
