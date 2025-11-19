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
