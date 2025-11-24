FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from the repo `app` folder into the image /app directory
# The build context is the repo root, so copy the `app` subfolder contents into /app
COPY app/ .

# Copy scripts folder for conversation_manager, query_enhancement, intent modules
COPY scripts/ ../scripts/

# Create data directory for persistent storage
RUN mkdir -p /app/data/chroma

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Build timestamp to force rebuild: 2025-11-24T23:20:00Z
# Run the application using main_simple which has the Zobot webhook integration with official Zoho response format
CMD ["uvicorn", "main_simple:app", "--host", "0.0.0.0", "--port", "8000"]