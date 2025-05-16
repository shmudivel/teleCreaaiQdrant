FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .env.prod .
COPY bustling-folio-439811-h8-539f8ab05fa7.json .

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "-m", "src.main"] 