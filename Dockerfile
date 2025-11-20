FROM python:3.11-slim

WORKDIR /app

# Install system deps required by some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["/bin/sh", "-c", "uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000} --loop asyncio"]
FROM python:3.11-slim

WORKDIR /app

# Install only essential dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir fastapi uvicorn[standard] requests pydantic python-dotenv

# Copy only the app code (minimal)
COPY app/main_simple.py ./app/
COPY app/salesiq_push.py ./app/

# Expose port
EXPOSE 8000

# Run the simplified API
CMD ["python", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
