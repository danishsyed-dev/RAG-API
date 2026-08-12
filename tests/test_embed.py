"""Unit tests for the embed module's chunking logic."""

from types import SimpleNamespace

import embed
from embed import chunk_text


class DummyCollection:
    def __init__(self):
        self.documents = None
        self.ids = None
        self.metadatas = None

    def upsert(self, documents, ids, metadatas):
        self.documents = documents
        self.ids = ids
        self.metadatas = metadatas


def test_chunk_small_text():
    """Text shorter than chunk_size should return a single chunk."""
    chunks = chunk_text("Short text.", chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == "Short text."


def test_chunk_empty_text():
    """Empty or whitespace-only text should return an empty list."""
    assert chunk_text("", chunk_size=500, overlap=50) == []
    assert chunk_text("   ", chunk_size=500, overlap=50) == []


def test_chunk_large_text():
    """Text larger than chunk_size should be split into multiple chunks."""
    text = "Word " * 200  # ~1000 characters
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    assert len(chunks) > 1


def test_chunk_no_empty_chunks():
    """All returned chunks should be non-empty strings."""
    text = "Hello world. " * 100
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    for chunk in chunks:
        assert chunk.strip() != ""


def test_chunk_covers_full_text():
    """The combined chunks should cover the entire original text."""
    text = "abcde " * 50  # 300 characters
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    # Every character in the original text should appear in at least one chunk
    combined = " ".join(chunks)
    for word in text.strip().split():
        assert word in combined


def test_chunk_respects_approximate_size():
    """Chunks should not vastly exceed the requested chunk_size."""
    text = "The quick brown fox jumps over the lazy dog. " * 50
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    for chunk in chunks:
        # Allow some slack for boundary snapping
        assert len(chunk) <= 200 * 1.5, f"Chunk too large: {len(chunk)} chars"


def test_chunk_size_one():
    """Edge case: chunk_size of 1 should still work without infinite loop."""
    chunks = chunk_text("abc", chunk_size=1, overlap=0)
    assert len(chunks) >= 1


def test_embed_file_uses_anydoc_for_rich_documents(tmp_path, monkeypatch):
    """Rich document formats should be converted through AnyDoc before embedding."""
    doc_path = tmp_path / "report.docx"
    doc_path.write_bytes(b"fake office document")

    monkeypatch.setattr(
        embed,
        "anydoc",
        SimpleNamespace(to_markdown=lambda path: "Converted markdown content"),
    )

    collection = DummyCollection()
    count = embed.embed_file(str(doc_path), collection, chunk_size=500, overlap=50)

    assert count == 1
    assert collection.documents == ["Converted markdown content"]
    assert collection.ids == ["report_chunk_0"]
    assert collection.metadatas[0]["source_format"] == "docx"
    assert collection.metadatas[0]["ingest_mode"] == "anydoc"
