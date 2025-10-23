# Backend Dockerfile for FastAPI service
FROM python:3.11-slim

# Setting work directory
WORKDIR /app

# Installing system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copying requirements
COPY requirements.txt .

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copying backend code
COPY backend.py .

# Exposing backend port
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
