"""Tests for the POST /query endpoint."""


def test_query_kubernetes(client):
    """Basic semantic query should return relevant content."""
    response = client.post("/query", json={"query": "What is Kubernetes?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    answer_lower = data["answer"].lower()
    assert "orchestration" in answer_lower or "container" in answer_lower


def test_query_returns_sources(client):
    """Response should include source documents."""
    data = client.post("/query", json={"query": "Tell me about Docker"}).json()
    assert len(data["sources"]) > 0
    source = data["sources"][0]
    assert "content" in source
    assert "id" in source


def test_query_custom_n_results(client):
    """n_results parameter should limit the number of sources."""
    data = client.post(
        "/query", json={"query": "What is Docker?", "n_results": 2}
    ).json()
    assert len(data["sources"]) <= 2


def test_query_empty_string_rejected(client):
    """Empty query string should fail validation."""
    response = client.post("/query", json={"query": ""})
    assert response.status_code == 422  # Pydantic validation error


def test_query_too_long_rejected(client):
    """Queries exceeding max length should fail validation."""
    response = client.post("/query", json={"query": "x" * 1001})
    assert response.status_code == 422


def test_query_n_results_zero_rejected(client):
    """n_results < 1 should fail validation."""
    response = client.post(
        "/query", json={"query": "test", "n_results": 0}
    )
    assert response.status_code == 422


def test_query_n_results_too_high_rejected(client):
    """n_results > 10 should fail validation."""
    response = client.post(
        "/query", json={"query": "test", "n_results": 11}
    )
    assert response.status_code == 422
