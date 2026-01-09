# 🔍 RAG-API

A lightweight **Retrieval-Augmented Generation (RAG)** API built with FastAPI, ChromaDB, and Ollama. Query your knowledge base with natural language and get intelligent responses powered by local LLMs.

## ✨ Features

- **🚀 Fast & Lightweight** - Built with FastAPI for high performance
- **📚 Vector Search** - ChromaDB for efficient document retrieval
- **🤖 Local LLM** - Uses Ollama with TinyLlama for fast, private inference
- **➕ Dynamic Knowledge Base** - Add documents on-the-fly via API
- **🔒 Privacy-First** - Everything runs locally, no external API calls

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| API Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Vector Database | [ChromaDB](https://www.trychroma.com/) |
| LLM | [Ollama](https://ollama.ai/) (TinyLlama) |

## 📋 Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed and running
- TinyLlama model pulled: `ollama pull tinyllama`

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/RAG-API.git
cd RAG-API
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Seed initial data (optional)
```bash
python embed.py
```

### 5. Start the server
```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Query Knowledge Base
```http
POST /query?q=your question here
```

**Example:**
```bash
curl -X POST "http://localhost:8000/query?q=What is Kubernetes?"
```

**Response:**
```json
{
  "answer": "Kubernetes is a container orchestration platform used to manage containers at scale."
}
```

### Add to Knowledge Base
```http
POST /add?text=your content here
```

**Example:**
```bash
curl -X POST "http://localhost:8000/add?text=Docker is a containerization platform."
```

**Response:**
```json
{
  "status": "success",
  "message": "Content added to knowledge base",
  "id": "uuid-here"
}
```

## 📁 Project Structure

```
RAG-API/
├── app.py          # FastAPI application with endpoints
├── embed.py        # Script to seed initial documents
├── k8s.txt         # Sample knowledge document
├── requirements.txt
└── README.md
```

## 🔧 Configuration

The application uses the following defaults:
- **ChromaDB path**: `./db`
- **Collection name**: `docs`
- **LLM model**: `tinyllama`

## 📄 License

MIT License - feel free to use this project for your own purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Made with ❤️ using FastAPI, ChromaDB, and Ollama
