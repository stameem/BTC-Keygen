# Backend Dockerfile for FastAPI service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for mysql-connector and reportlab)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend.py .

# Expose backend port
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
