from fastapi import FastAPI
import chromadb
import ollama

app = FastAPI(title="RAG API", description="A RAG-based Question Answering API powered by Ollama and ChromaDB")
chroma = chromadb.PersistentClient(path="./db")
collection = chroma.get_or_create_collection("docs")

@app.get("/")
def root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to the RAG API!",
        "endpoints": {
            "POST /query": "Ask a question (e.g., /query?q=What is Kubernetes?)",
            "POST /add": "Add knowledge to the database (e.g., /add?text=Your text here)",
            "GET /docs": "Interactive API documentation (Swagger UI)"
        },
        "status": "running"
    }

@app.post("/query")
def query(q: str):
    results = collection.query(query_texts=[q], n_results=1)
    context = results["documents"][0][0] if results["documents"] else ""

    answer = ollama.generate(
        model="tinyllama",
        prompt=f"Context:\n{context}\n\nQuestion: {q}\n\nAnswer clearly and concisely:"
    )

    return {"answer": answer["response"]}

#Dynamic Content to Your Knowledge Base
@app.post("/add")
def add_knowledge(text: str):
    """Add new content to the knowledge base dynamically."""
    try:
        # Generate a unique ID for this document
        import uuid
        doc_id = str(uuid.uuid4())
        
        # Add the text to Chroma collection
        collection.add(documents=[text], ids=[doc_id])
        
        return {
            "status": "success",
            "message": "Content added to knowledge base",
            "id": doc_id
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
