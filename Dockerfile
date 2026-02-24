FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY accessai/ ./accessai/
COPY .env.example .env  # Template for env variables

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "accessai.main:app", "--host", "0.0.0.0", "--port", "8080"]
