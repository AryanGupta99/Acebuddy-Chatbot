# AceBuddy RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for AceBuddy ticket automation using FastAPI, ChromaDB, and Ollama.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Docker Desktop
- Git
- Ollama

### 2. Install Python Dependencies
```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Ollama
```powershell
# Pull a model (choose one)
ollama pull mistral
ollama pull llama2
ollama pull phi
```

### 4. Prepare Data
- Copy your KB articles to `data/kb/` (as .txt files)
- Copy `real_user_issues.csv` to the `data/` directory

### 5. Complete Data Preparation & Ingestion Pipeline

We provide an **automated complete pipeline** that handles data cleaning, PII redaction, embedding generation, and vector DB ingestion:

```powershell
# Start Docker services first
docker-compose up -d

# Run the complete pipeline (recommended)
.\run_complete_pipeline.ps1

# Or skip API testing for faster execution
.\run_complete_pipeline.ps1 -SkipApiTest
```

**What the pipeline does:**
1. **Data Preparation** (`scripts/data_preparation.py`)
   - Cleans KB files (UTF-8 normalization, whitespace fixes)
   - Detects & redacts PII (emails, phones, SSN, credit cards, IPs, DOB, passwords, API keys)
   - Removes duplicates (SHA256-based)
   - Scores document quality (0-1 scale)
   - Chunks text semantically (500 chars per chunk)
   - **Output:** `data/prepared/{documents_cleaned.json, chunks_for_rag.json, preparation_report.json}`

2. **RAG Ingestion** (`scripts/rag_ingestion.py`)
   - Loads cleaned chunks
   - Generates embeddings (SentenceTransformer or offline mode)
   - Filters by quality score (0.3+ threshold)
   - Indexes vectors in ChromaDB
   - **Output:** `acebuddy_kb` collection with 100+ vectors

3. **LLM Testing** (Optional)
   - Tests 5 sample queries
   - Verifies context retrieval
   - Validates LLM responses

**Individual Pipeline Commands:**

```powershell
# Just prepare data (clean, deduplicate, score quality, chunk)
python scripts/data_preparation.py

# Just ingest into ChromaDB (generate embeddings, store vectors)
python scripts/rag_ingestion.py

# Full pipeline with orchestration
python scripts/full_pipeline.py

# Skip API testing
python scripts/full_pipeline.py --skip-api-test
```

### 6. Verify Data Preparation Results

After running the pipeline, check the quality report:

```powershell
# View the preparation report
Get-Content data/prepared/preparation_report.json | ConvertFrom-Json | Format-Table

# See the cleaned documents
Get-Content data/prepared/documents_cleaned.json | ConvertFrom-Json | Select-Object -First 1

# Check number of chunks created
(Get-Content data/prepared/chunks_for_rag.json | ConvertFrom-Json).Count
```

### 7. Ingest Data (Manual Method)

If you prefer manual ingestion instead of the automated pipeline:

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run data ingestion
python scripts/ingest_data.py
```

### 8. Run the Application

#### Option A: Local Development
```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run FastAPI app
cd app
python main.py
```

#### Option B: Docker
```powershell
# Build and run with Docker Compose
docker-compose up --build
```

### 9. Test the API

The API will be available at:
- FastAPI: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ChromaDB: http://localhost:8001

#### Test chat endpoint:
```powershell
# Using curl
curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -d "{\"query\": \"How do I reset my password?\", \"user_id\": \"test_user\"}"
```

#### Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "How do I reset my password?", "user_id": "test_user"}
)
print(response.json())
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /chat` - Main chat endpoint
- `POST /ingest` - Trigger data ingestion (to be implemented)

## Project Structure

```
AceBuddy-RAG/
├── app/                 # FastAPI application
│   ├── main.py         # Main application file
│   └── Dockerfile      # Docker configuration
├── data/               # Data storage
│   ├── kb/            # Knowledge base files (.txt)
│   └── chroma/        # ChromaDB storage
├── scripts/           # Utility scripts
│   └── ingest_data.py # Data ingestion script
├── tests/             # Test files
├── requirements.txt   # Python dependencies
├── docker-compose.yml # Docker orchestration
├── .env              # Environment variables
└── README.md         # This file
```

## Configuration

Edit `.env` file to configure:
- `OLLAMA_MODEL` - Which Ollama model to use
- `VECTOR_DB_COLLECTION` - ChromaDB collection name
- `FASTAPI_HOST` and `FASTAPI_PORT` - Server configuration

## Migration to Cloud/Server

1. Copy entire project directory
2. Install prerequisites on target machine
3. Run setup commands
4. Update `.env` for production settings
5. Use Docker for easier deployment

## Troubleshooting

### Common Issues:
1. **Import errors**: Make sure virtual environment is activated and dependencies are installed
2. **Ollama not responding**: Check if Ollama service is running
3. **ChromaDB errors**: Delete `data/chroma/` directory and re-run ingestion
4. **Docker issues**: Ensure Docker Desktop is running

### Logs:
- Application logs are printed to console
- For Docker: `docker-compose logs -f`

## Next Steps

1. Add more KB content to `data/kb/`
2. Implement webhook integration with Zoho SalesIQ
3. Add authentication and rate limiting
4. Deploy to production server/cloud
5. Add monitoring and analytics

## Persistence and Backups (Chroma)

Important: Chroma stores its data under the container path `/chroma/chroma` (inside the container). By default the project uses a named Docker volume so data survives container rebuilds. Do NOT mount Chroma data onto a OneDrive-synced folder — this can corrupt the DB.

Recommended default (docker-compose): named volume `chroma_data` is used and mapped to `/chroma/chroma` inside the Chroma container. To back up or restore use the helper scripts in `scripts/`:

PowerShell - create a backup of the Chroma volume:
```powershell
.\scripts\backup_chroma.ps1
```

PowerShell - restore a backup tar into the Chroma volume:
```powershell
#.\scripts\restore_chroma.ps1 -BackupFile .\backups\chroma_backup_20251111_120000.tar.gz
```

If you prefer storing DB files directly on the host (not recommended if your repo is on OneDrive), update `docker-compose.yml` and replace the named volume with a bind mount to a safe folder (example: `C:/acebuddy_data/chroma`). Example (commented in `docker-compose.yml`):

```yaml
        volumes:
            - chroma_data:/chroma/chroma
            # or bind to host (NOT in OneDrive):
            # - C:/acebuddy_data/chroma:/chroma/chroma
```

Also: keep your raw KB and transcript files in `data/kb/` and `data/raw/` so you can always re-ingest into a fresh Chroma instance if needed.