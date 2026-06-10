"""Legacy semantic test — runs against a live server.

For the primary test suite, use: pytest tests/ -v

This script is kept for quick manual smoke-testing against a running instance.
"""

import requests


def test_kubernetes_query():
    response = requests.post(
        "http://127.0.0.1:8000/query",
        json={"query": "What is Kubernetes?"},
    )

    if response.status_code != 200:
        raise Exception(f"Server returned {response.status_code}: {response.text}")

    data = response.json()
    answer = data["answer"]

    # Check for key concepts
    assert "orchestration" in answer.lower(), "Missing 'orchestration' keyword"
    assert "container" in answer.lower(), "Missing 'container' keyword"

    print("✅ Kubernetes query test passed")
    print(f"   Sources: {len(data.get('sources', []))} document(s)")


if __name__ == "__main__":
    test_kubernetes_query()
    print("All semantic tests passed!")
