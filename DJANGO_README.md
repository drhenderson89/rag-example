# RAG Chat Interface - Django Demo

A web-based Retrieval-Augmented Generation (RAG) chat application built with Django, LangChain, ChromaDB, and Ollama. This demo application allows users to upload documents and ask questions with AI-powered responses enhanced by document context.

## 🚀 Features

- **Web-based Chat Interface**: Clean, modern UI for interacting with the RAG system
- **Document Upload**: Support for PDF, DOCX, CSV, and TXT files
- **Semantic Chunking**: Intelligent document splitting that preserves context and meaning
  - Text/DOCX: Embedding-based semantic boundary detection
  - PDF: Hierarchical splitting respecting document structure
  - CSV: Row-optimized chunking
- **Metadata Enrichment**: Every chunk includes source, timestamp, language, word/char count, content hash
- **Smart Deduplication**: Automatic detection and removal of duplicate chunks via content hashing
- **Vector Search**: ChromaDB for efficient semantic search
- **LLM Integration**: Ollama for local LLM inference
- **Docker Support**: Fully containerized with Docker Compose
- **RAG Context**: Automatically uses uploaded documents to enhance responses
- **Database Analytics**: View chunk counts, language distribution, and file type statistics

## 📋 Prerequisites

- Docker and Docker Compose installed on your system
- At least 8GB of RAM (for running Ollama models)
- Basic understanding of Docker and Django

## 🛠️ Project Structure

```
rag-example/
├── ragproject/           # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── ragapp/              # Main Django application
│   ├── templates/       # HTML templates
│   ├── views.py         # View logic
│   ├── urls.py          # URL routing
│   ├── rag_handler.py   # RAG logic
│   ├── model_handler.py # LLM interaction
│   └── signals.py       # Initialization logic
├── ingest/              # Folder for uploaded documents
├── database/            # ChromaDB vector store
├── config.json          # RAG configuration
├── docker-compose.yml   # Docker orchestration
├── dockerfile           # Django container definition
├── requirements.txt     # Python dependencies
└── manage.py            # Django management script
```

## 🚀 Quick Start

### 1. Clone or Navigate to the Project

```bash
cd d:\Docs\Rockport\RAG\rag-example
```

### 2. Start the Application

```bash
docker-compose up --build
```

This will:
- Build the Django application container
- Pull and start the Ollama container
- **Automatically download the llama3.2 model** (first run only, ~5-10 minutes)
- Set up the necessary volumes and networks
- Start the web interface on port 8000

**Note**: The first startup will take longer as it downloads the LLM model (~7GB). Subsequent starts are instant.

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

## 📖 How to Use

### Uploading Documents

1. **Via Click**: Click on the "Upload Documents" area in the sidebar
2. **Via Drag & Drop**: Drag files directly onto the upload area

Supported formats: `.pdf`, `.docx`, `.csv`, `.txt`

### Chatting

1. Type your question in the input box at the bottom
2. Press Enter or click "Send"
3. The AI will respond using:
   - **RAG Mode**: If documents are uploaded, answers are enhanced with document context
   - **Normal Mode**: If no documents exist, standard LLM responses

### Features

- **Document Counter**: Shows how many documents are in the database
- **RAG Indicator**: System messages indicate when RAG context was used
- **Real-time**: Immediate processing and responses

## ⚙️ Configuration

### Changing the Model

The default model is `llama3.2`. To use a different model:

1. Edit [docker-compose.yml](docker-compose.yml):
   ```yaml
   # In the ollama-puller service, change:
   ollama pull llama3.2
   # to your preferred model, e.g.:
   ollama pull llama3.2:1b
   
   # Also update the web service environment:
   - MODEL_NAME=llama3.2:1b
   ```

2. Remove the old model (optional):
   ```bash
   docker exec -it ollama ollama rm llama3.2
   ```

**Available models:**
- `llama3.2` (default, ~7GB, 7B parameters)
- `llama3.2:1b` (smaller, ~1.3GB, faster, less accurate)
- `mistral` (alternative, good performance)
- `codellama` (optimized for code)

### config.json

Customize RAG behavior by editing config.json:

```json
{
    "rag_options": {
        "delete_file_after_ingestion": false,
        "clear_database_on_start": false,
        "similarity_threshold": 0.3,
        "results_to_return": 2
    },
    "llm_options": {
        "system_prompt": "You are an assistant...",
        "temperature": 0.8,
        "tokens_to_generate": 256
    }
}
```

**Options:**
- `similarity_threshold`: Minimum relevance score (0-1) for document chunks
- `results_to_return`: Number of relevant document chunks to use
- `temperature`: LLM creativity (0=deterministic, 1=creative)
- `tokens_to_generate`: Maximum response length
- `chunking_strategy`: Set to "semantic" (default) for intelligent chunking
- `semantic_breakpoint_threshold`: Percentile for semantic splits (80 = split at top 20% differences)

**Learn more:**
- Semantic Chunking: [SEMANTIC_CHUNKING.md](SEMANTIC_CHUNKING.md)
- Metadata Enrichment: [METADATA_ENRICHMENT.md](METADATA_ENRICHMENT.md)

### Environment Variables

Configure via docker-compose.yml:

```yaml
environment:
  - OLLAMA_ADDRESS=http://ollama:11434
  - MODEL_NAME=llama3.2
  - INGESTION_FOLDER=/app/ingest
  - DATABASE_FOLDER=/app/database
```

## 🔧 Development Setup

### Running Locally (Without Docker)

1. **Install Python 3.11+**

2. **Create Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run Migrations**
```bash
python manage.py migrate
```

5. **Start Ollama Separately**
```bash
# Download and run Ollama from https://ollama.ai
ollama pull llama3.2
ollama serve
```

6. **Update Settings**
Edit ragproject/settings.py:
```python
OLLAMA_ADDRESS = 'http://127.0.0.1:11434'
```

7. **Run Django Server**
```bash
python manage.py runserver
```

Access at `http://localhost:8000`

## 🐛 Troubleshooting

### Container Issues

**Problem**: Ollama container won't start
```bash
# Check logs
docker logs ollama

# Restart
docker-compose restart ollama
```

**Problem**: Django can't connect to Ollama
- Ensure Ollama container is running: `docker ps`
- Check if model is downloaded: `docker exec -it ollama ollama list`
- Verify network: Both containers should be on same network

### Model Issues

**Problem**: Model download seems stuck
```bash
# Check ollama-puller logs
docker logs ollama_puller

# If needed, manually pull the model
docker exec -it ollama ollama pull llama3.2

# Verify model is downloaded
docker exec -it ollama ollama list
```

**Problem**: "Model not found" error after startup
- Check if download completed: `docker logs ollama_puller`
- Manually download if needed: `docker exec -it ollama ollama pull llama3.2`
- Restart web container: `docker-compose restart web`

**Problem**: Out of memory
- Try a smaller model: `llama3.2:1b`
- Increase Docker memory allocation (Docker Desktop → Settings → Resources)

### Upload Issues

**Problem**: File upload fails
- Check file size (max 10MB by default)
- Verify file format is supported
- Check logs: `docker logs rag_django`

### Database Issues

**Problem**: ChromaDB errors
```bash
# Stop containers
docker-compose down

# Remove database volume
docker volume rm rag-example_ollama_data

# Restart
docker-compose up --build
```

## 📚 API Endpoints

- `GET /` - Main chat interface
- `POST /upload/` - Upload documents
- `POST /query/` - Submit queries
- `GET /status/` - System status

## 🔒 Security Notes

**This is a DEV DEMO - NOT production ready:**

- Django `DEBUG = True` (exposes error details)
- Default `SECRET_KEY` (should be randomized)
- No authentication or user management
- No rate limiting
- `ALLOWED_HOSTS = ['*']` (should be restricted)
- CSRF protection enabled but basic

**For production, implement:**
- Environment-based configuration
- Proper secret management
- User authentication
- HTTPS/SSL
- Rate limiting
- Input validation
- Logging and monitoring

## 🛑 Stopping the Application

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (clears database)
docker-compose down -v
```

## 📝 Additional Notes

### Model Selection

Choose based on your hardware:
- **8GB RAM**: `llama3.2:1b`
- **16GB RAM**: `llama3.2` (default)
- **32GB+ RAM**: `llama3.2:7b` or larger models

### Performance Tips

- Use SSDs for better vector store performance
- Allocate sufficient RAM to Docker
- Keep document sizes reasonable (<10MB)
- **Semantic chunking** adapts to document type automatically:
  - Text/DOCX uses embedding-based boundary detection for best quality
  - PDFs use structural splitting (sections → paragraphs → sentences)
  - Adjust `semantic_breakpoint_threshold` in [config.json](config.json) for chunk size tuning

### Data Persistence

Data is persisted in Docker volumes:
- `ollama_data`: Ollama models
- Local `database/`: ChromaDB vectors
- Local `ingest/`: Uploaded documents (if not deleted)

## 🤝 Contributing

This is a demo project for learning purposes. Feel free to:
- Modify the code
- Add new features
- Experiment with different models
- Improve the UI

## 📄 License

This project is for educational and demonstration purposes.

## 🙏 Acknowledgments

- **LangChain**: Framework for LLM applications
- **ChromaDB**: Vector database
- **Ollama**: Local LLM runtime
- **Django**: Web framework

---

**Need Help?** Check the logs:
```bash
# Django logs
docker logs rag_django

# Ollama logs
docker logs ollama

# Follow logs in real-time
docker-compose logs -f
```

## 📋 Original CLI Version

The original command-line version is preserved in app.py. This Django version provides the same functionality through a web interface.
