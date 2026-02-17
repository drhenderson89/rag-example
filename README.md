# RAG Web Application with Django & Ollama

A learning-focused Retrieval Augmented Generation (RAG) web application built with Django, LangChain, ChromaDB, and Ollama. This project demonstrates modern RAG techniques including semantic chunking, metadata enrichment, and conversational AI with a clean, understandable codebase.

> **⚠️ Educational Project**: This is a development and learning tool designed to help understand RAG concepts and implementation. It is **not production-ready** and should be used for educational purposes, experimentation, and local development only.

## 🌟 Features

- **Web-Based Interface**: Modern, responsive UI with drag-and-drop file upload
- **Semantic Chunking**: Intelligent document splitting using embeddings for better context preservation
- **Multiple Document Support**: Upload single or multiple files simultaneously (PDF, DOCX, CSV, TXT)
- **Smart Deduplication**: Content hash-based duplicate detection to prevent redundant storage
- **Rich Metadata**: Automatic extraction of language, word count, file type, and more
- **Real-Time Statistics**: Live database stats showing chunks, languages, and document counts
- **Persistent Storage**: ChromaDB vector database with permanent storage
- **Docker Compose Ready**: Complete containerized deployment with Ollama and Django services
- **Automatic Model Download**: Ollama model automatically downloaded on first startup
- **Clean Architecture**: Well-organized Django project structure with reusable components

## 📋 Prerequisites

### For Docker Deployment (Recommended)
- [Docker](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0+)
- 8GB+ RAM recommended for default `llama3.2` model
- **For 4-8GB RAM**: Use smaller models like `llama3.2:1b` (see [Advanced Configuration](#-advanced-configuration))

### For Local Development
- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- 8GB+ RAM recommended (4GB+ with smaller models)

## 🚀 Quick Start with Docker (Recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/yussufbiyik/langchain-chromadb-rag-example.git
cd langchain-chromadb-rag-example
```

### 2. Build the Docker Image
```bash
docker build -t rag_django:1.0.0 .
```

### 3. Start the Services
```bash
docker-compose up
```

The application will be available at **http://localhost:8000**

> **Note**: On first startup, Ollama will automatically download the `llama3.2` model (~2GB). This may take several minutes depending on your connection.

> **💡 Tip for Limited Hardware**: If you have less than 8GB RAM, modify `ollama-init.sh` to use `llama3.2:1b` (only 1.3GB) before starting. See [Using Smaller Models](#using-smaller-models-for-limited-hardware).

### 4. Stop the Services
```bash
docker-compose down
```

To remove all data including the database and models:
```bash
docker-compose down -v
```

## 💻 Local Development Setup

### 1. Clone and Install Dependencies
```bash
git clone https://github.com/yussufbiyik/langchain-chromadb-rag-example.git
cd langchain-chromadb-rag-example
pip install -r requirements.txt
```

### 2. Install and Start Ollama
Download and install from [ollama.ai](https://ollama.ai/), then:
```bash
ollama serve
ollama pull llama3.2
```

### 3. Run Django Development Server
```bash
python manage.py runserver
```

The application will be available at **http://localhost:8000**

## ⚙️ Configuration

Edit `config.json` to customize behavior:

```json
{
    "rag_options": {
        "delete_file_after_ingestion": true,
        "clear_database_on_start": false,
        "similarity_threshold": 0.3,
        "results_to_return": 2,
        "chunking_strategy": "semantic",
        "semantic_breakpoint_threshold": 80
    },
    "llm_options": {
        "system_prompt": "You are an assistant for question-answering tasks...",
        "temperature": 0.8,
        "tokens_to_generate": 2048
    }
}
```

### Environment Variables

For Docker deployment, configure in `docker-compose.yml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | Ollama model to use | `llama3.2` |
| `OLLAMA_ADDRESS` | Ollama server URL | `http://ollama:11434` |
| `INGESTION_FOLDER` | Document upload directory | `/app/ingest` |
| `DATABASE_FOLDER` | ChromaDB storage path | `/app/database` |

## 📖 Usage

### Uploading Documents

1. **Drag & Drop**: Drag one or multiple files onto the upload area
2. **Click to Upload**: Click the upload area to browse and select files
3. **Supported Formats**: PDF, DOCX, CSV, TXT

### Querying with RAG

1. Type your question in the chat input
2. The system retrieves relevant document chunks using semantic similarity
3. The LLM generates a response based on your documents and the query

### Managing the Database

- **View Statistics**: Document count, chunk count, languages, and file types are displayed in real-time
- **Clear Database**: Click the "Clear Database" button in the sidebar (requires confirmation)

## 🏗️ Architecture

```
rag-example/
├── ragproject/          # Django project settings
│   ├── settings.py      # Configuration with RAG-specific settings
│   └── urls.py          # Root URL routing
├── ragapp/              # Main Django application
│   ├── views.py         # API endpoints (upload, query, status, clear)
│   ├── rag_handler.py   # RAG logic with semantic chunking
│   ├── model_handler.py # Ollama LLM integration
│   ├── signals.py       # Global handler initialization
│   └── templates/       # Web UI templates
├── dockerfile           # Django container definition
├── docker-compose.yml   # Multi-service orchestration
├── ollama-init.sh       # Ollama startup script
├── requirements.txt     # Python dependencies
└── config.json          # RAG and LLM configuration
```

### Key Components

- **RAGHandler**: Manages document loading, semantic chunking, metadata enrichment, and deduplication
- **ModelHandler**: Interfaces with Ollama for LLM responses with RAG context
- **ChromaDB**: Vector database for semantic search with FastEmbed embeddings
- **Django Views**: RESTful endpoints for document upload, querying, and statistics

## 🔧 Advanced Configuration

### Using a Different Model

Edit `docker-compose.yml` and change the `MODEL_NAME` environment variable:

```yaml
environment:
  - MODEL_NAME=mistral  # or llama2, codellama, etc.
```

Also update the model in `ollama-init.sh`:
```bash
ollama pull mistral
```

### Using Smaller Models for Limited Hardware

For machines with less RAM (4-8GB) or lower-end CPUs, use a smaller model variant. Edit `ollama-init.sh` to pull a lightweight model:

```bash
# Replace the default model pull with a smaller variant
ollama pull llama3.2:1b  # Only ~1.3GB, suitable for 4GB+ RAM
```

**Recommended small models:**
- `llama3.2:1b` - 1.3GB, fastest, good for basic queries
- `phi3:mini` - 2.3GB, balanced performance and size
- `gemma:2b` - 1.7GB, efficient and accurate

Also update `MODEL_NAME` in `docker-compose.yml`:
```yaml
environment:
  - MODEL_NAME=llama3.2:1b
```

### Adjusting Chunk Size and Overlap

Modify the splitters in `ragapp/rag_handler.py`:

```python
self.semantic_splitter = SemanticChunker(
    self.embedding_function,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=80  # Adjust 0-100
)
```

### Changing Similarity Threshold

In `config.json`, adjust `similarity_threshold` (0.0-1.0):
- Lower values: More permissive, returns more results
- Higher values: Stricter, returns only highly relevant results

## 🐛 Troubleshooting

### Docker Issues

**Container fails to start:**
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache
```

**Ollama model not downloading:**
```bash
# Check Ollama container logs
docker-compose logs ollama

# Manually pull model
docker-compose exec ollama ollama pull llama3.2
```

### Local Development Issues

**ChromaDB persistence errors:**
```bash
# Remove and recreate database folder
rm -rf database/
mkdir database
```

**Ollama connection refused:**
```bash
# Verify Ollama is running
ollama list

# Restart Ollama service
ollama serve
```

## 🤝 Contributing

Contributions are welcome! This project aims to provide clean, understandable code for learning RAG concepts and techniques.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available for educational purposes.

## 🙏 Acknowledgments

**Forked from**: [yussufbiyik/langchain-chromadb-rag-example](https://github.com/yussufbiyik/langchain-chromadb-rag-example) - Thank you for the excellent foundation and clean CLI implementation that inspired this web-based version.

**Built with:**
- [LangChain](https://www.langchain.com/) for RAG orchestration
- [Ollama](https://ollama.ai/) for local LLM inference
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Django](https://www.djangoproject.com/) web framework

---

**Note**: This educational project evolved from a CLI-based RAG example to a web application with advanced features like semantic chunking and metadata enrichment. The original CLI version is preserved in `app.py` for reference.
