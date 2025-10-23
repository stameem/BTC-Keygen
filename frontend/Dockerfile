# Frontend Dockerfile for NiceGUI service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code
COPY frontend.py .

# Expose frontend port
EXPOSE 8081

# Run NiceGUI frontend
CMD ["python", "frontend.py"]
