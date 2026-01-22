# 🔍 RAG-API

[![CI Pipeline](https://github.com/danishsyed-dev/RAG-API/actions/workflows/ci.yml/badge.svg)](https://github.com/danishsyed-dev/RAG-API/actions/workflows/ci.yml)

A lightweight **Retrieval-Augmented Generation (RAG)** API built with FastAPI, ChromaDB, and Ollama. Query your knowledge base with natural language and get intelligent responses powered by local LLMs.

## ✨ Features

- **🚀 Fast & Lightweight** - Built with FastAPI for high performance
- **📚 Vector Search** - ChromaDB for efficient document retrieval
- **🤖 Local LLM** - Uses Ollama with TinyLlama for fast, private inference
- **☸️ Kubernetes Ready** - Full K8s deployment manifests included
- **🧪 CI/CD Pipeline** - Automated testing with GitHub Actions
- **🔒 Privacy-First** - Everything runs locally, no external API calls

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| API Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Vector Database | [ChromaDB](https://www.trychroma.com/) |
| LLM | [Ollama](https://ollama.ai/) (TinyLlama) |
| Container Orchestration | [Kubernetes](https://kubernetes.io/) / [Minikube](https://minikube.sigs.k8s.io/) |
| CI/CD | [GitHub Actions](https://github.com/features/actions) |

## 📋 Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai/) installed and running
- TinyLlama model pulled: `ollama pull tinyllama`
- (Optional) [Minikube](https://minikube.sigs.k8s.io/) for Kubernetes deployment

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/danishsyed-dev/RAG-API.git
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

## ☸️ Kubernetes Deployment

Deploy to a local Minikube cluster:

### 1. Start Minikube
```bash
minikube start
```

### 2. Build the image inside Minikube
```bash
minikube image build -t rag-api:latest .
```

### 3. Apply Kubernetes manifests
```bash
kubectl apply -f k8s/
```

### 4. Pull the LLM model
```bash
kubectl exec deploy/ollama -- ollama pull tinyllama
```

### 5. Access the API
```bash
kubectl port-forward svc/rag-api 8000:8000
```

Your API is now available at `http://127.0.0.1:8000`

## 🧪 Testing

Run semantic tests to verify the RAG system:

```bash
python semantic_test.py
```

### Mock LLM Mode (for CI)
```bash
USE_MOCK_LLM=1 uvicorn app:app --reload
```

## 📁 Project Structure

```
RAG-API/
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI pipeline
├── k8s/
│   ├── ollama.yaml       # Ollama deployment & service
│   └── rag-api.yaml      # RAG API deployment & service
├── app.py                # FastAPI application
├── embed.py              # Script to seed initial documents
├── semantic_test.py      # Semantic quality tests
├── Dockerfile            # Container image definition
├── k8s.txt               # Sample knowledge document
├── requirements.txt
└── README.md
```

## 🔧 Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| ChromaDB path | `./db` | Vector database storage location |
| Collection name | `docs` | ChromaDB collection name |
| LLM model | `tinyllama` | Ollama model for inference |
| Mock LLM | `USE_MOCK_LLM=0` | Set to `1` for CI testing |

## 🔄 CI/CD Pipeline

The project includes a GitHub Actions workflow that:
1. Triggers on changes to `app.py`, `embed.py`, or `k8s.txt`
2. Rebuilds embeddings
3. Runs the API in mock mode
4. Executes semantic tests to verify RAG quality

## 📄 License

MIT License - feel free to use this project for your own purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Made with ❤️ using FastAPI, ChromaDB, Ollama, and Kubernetes
