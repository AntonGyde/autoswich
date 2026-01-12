FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Install system dependencies in a single layer and clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends libportaudio2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

EXPOSE 8000

CMD ["uvicorn","webapp:app","--host","0.0.0.0","--port","8000"]
