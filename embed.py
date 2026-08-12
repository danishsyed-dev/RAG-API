"""Document ingestion script with chunking support.

Reads text files, splits them into overlapping chunks, and stores
embeddings in ChromaDB.

Usage:
    python embed.py                              # Embed default k8s.txt
    python embed.py --file docs/guide.txt        # Embed a specific file
    python embed.py --dir ./documents            # Embed all files in a directory
    python embed.py --chunk-size 300 --overlap 50
"""

import argparse
import logging
import os
from pathlib import Path

import chromadb

from config import settings

try:
    import anydoc
except ImportError:
    anydoc = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("rag-embed")

TEXT_EXTENSIONS = {".txt", ".md"}
ANYDOC_EXTENSIONS = {
    ".doc",
    ".docm",
    ".docx",
    ".epub",
    ".odp",
    ".ods",
    ".odt",
    ".pdf",
    ".ppt",
    ".pptm",
    ".pptx",
    ".pps",
    ".ppsm",
    ".ppsx",
    ".pot",
    ".rtf",
    ".xls",
    ".xlsb",
    ".xlsm",
    ".xlsx",
    ".csv",
}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | ANYDOC_EXTENSIONS


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split *text* into overlapping chunks, breaking at natural boundaries.

    Tries to break at paragraph (``\\n\\n``) or sentence (``. ``) boundaries
    when possible.  Falls back to the raw character offset otherwise.

    Returns an empty list for blank / whitespace-only input.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to snap to a natural boundary so chunks read well
        if end < len(text):
            # Prefer paragraph breaks
            last_para = chunk.rfind("\n\n")
            if last_para > chunk_size * 0.3:
                end = start + last_para + 2
                chunk = text[start:end]
            else:
                # Fall back to sentence breaks
                last_sentence = chunk.rfind(". ")
                if last_sentence > chunk_size * 0.3:
                    end = start + last_sentence + 2
                    chunk = text[start:end]

        stripped = chunk.strip()
        if stripped:
            chunks.append(stripped)

        start = end - overlap

    return chunks


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------
def load_document_text(path: Path) -> str | None:
    """Load text from a supported file, converting rich formats to Markdown."""
    suffix = path.suffix.lower()

    if suffix in TEXT_EXTENSIONS:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    if suffix in ANYDOC_EXTENSIONS:
        if anydoc is None:
            logger.warning(
                "Skipping %s because firecrawl-anydoc is not installed.",
                path,
            )
            return None

        try:
            return anydoc.to_markdown(str(path))
        except Exception as exc:
            logger.warning("Failed to convert %s with AnyDoc: %s", path, exc)
            return None

    logger.warning("Skipping unsupported file type: %s", path)
    return None


def embed_file(
    filepath: str,
    collection,
    chunk_size: int,
    overlap: int,
) -> int:
    """Read, chunk, and embed a single file.  Returns the number of chunks stored."""
    path = Path(filepath)

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.warning("Skipping unsupported file type: %s", path)
        return 0

    logger.info("Processing: %s", path)

    text = load_document_text(path)
    if text is None:
        return 0

    if not text.strip():
        logger.warning("Skipping empty file: %s", path)
        return 0

    chunks = chunk_text(text, chunk_size, overlap)

    ids = []
    documents = []
    metadatas = []

    for idx, chunk in enumerate(chunks):
        doc_id = f"{path.stem}_chunk_{idx}"
        ids.append(doc_id)
        documents.append(chunk)
        metadatas.append(
            {
                "source": path.name,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "source_format": path.suffix.lower().lstrip("."),
                "ingest_mode": "anydoc" if path.suffix.lower() in ANYDOC_EXTENSIONS else "plain_text",
            }
        )

    collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
    logger.info("  → Embedded %d chunk(s) from %s", len(chunks), path.name)

    return len(chunks)


def embed_directory(
    dirpath: str,
    collection,
    chunk_size: int,
    overlap: int,
) -> int:
    """Embed every supported file found (recursively) under *dirpath*."""
    total = 0
    dir_path = Path(dirpath)

    for ext in sorted(SUPPORTED_EXTENSIONS):
        for filepath in sorted(dir_path.rglob(f"*{ext}")):
            total += embed_file(str(filepath), collection, chunk_size, overlap)

    return total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed documents into ChromaDB for the RAG-API.",
    )
    parser.add_argument("--file", type=str, help="Path to a single file to embed.")
    parser.add_argument(
        "--dir", type=str, help="Path to a directory of files to embed (recursive)."
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=settings.chunk_size,
        help=f"Characters per chunk (default: {settings.chunk_size}).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=settings.chunk_overlap,
        help=f"Overlap between chunks (default: {settings.chunk_overlap}).",
    )

    args = parser.parse_args()

    client = chromadb.PersistentClient(path=settings.chromadb_path)
    collection = client.get_or_create_collection(settings.collection_name)

    total_chunks = 0

    if args.dir:
        total_chunks = embed_directory(
            args.dir, collection, args.chunk_size, args.overlap
        )
    elif args.file:
        total_chunks = embed_file(
            args.file, collection, args.chunk_size, args.overlap
        )
    else:
        # Default: embed k8s.txt for backward compatibility
        default_file = os.path.join(os.path.dirname(__file__) or ".", "k8s.txt")
        if os.path.exists(default_file):
            total_chunks = embed_file(
                default_file, collection, args.chunk_size, args.overlap
            )
        else:
            logger.error("No file specified and default 'k8s.txt' not found.")
            return

    logger.info("✅ Done! Embedded %d chunk(s) total.", total_chunks)


if __name__ == "__main__":
    main()
