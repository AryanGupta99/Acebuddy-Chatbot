FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (use app/ as the service root)
COPY app/ ./
COPY scripts/ ./scripts/
COPY data/ ./data/

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the full RAG application (main.py) so the service uses the vector DB + LLM pipeline
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
