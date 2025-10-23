# Frontend for NiceGUI service
FROM python:3.11-slim

# Setting work directory
WORKDIR /app

# Installing system dependencies
RUN apt-get update && apt-get install -y \
    gcc libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Installing Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copying frontend code
COPY frontend.py .

# Exposing frontend port
EXPOSE 8081

# Running NiceGUI frontend
CMD ["python", "frontend.py"]
