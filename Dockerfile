# syntax=docker/dockerfile:1
# ------------------------------------------------------------------------------
# WayMate AI Agent Dockerfile
# Installs Ollama, downloads qwen2.5:0.5b during image build, and runs FastAPI
# ------------------------------------------------------------------------------
FROM python:3.10-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    zstd \
    build-essential \
    python3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install official Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Configure Ollama models path
ENV OLLAMA_MODELS=/root/.ollama/models \
    OLLAMA_HOST=0.0.0.0:11434

# Copy python dependencies
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Download model qwen2.5:0.5b during Docker image build
RUN ollama serve > /tmp/ollama_build.log 2>&1 & \
    BUILD_PID=$! && \
    echo "Waiting for build-time Ollama daemon..." && \
    READY=false && \
    for i in $(seq 1 30); do \
        if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then \
            echo "Build-time Ollama is running."; \
            READY=true; \
            break; \
        fi; \
        sleep 1; \
    done && \
    if [ "$READY" = "false" ]; then \
        echo "Ollama failed to start in time. Log:"; \
        cat /tmp/ollama_build.log; \
        exit 1; \
    fi && \
    echo "Downloading and caching qwen2.5:0.5b model..." && \
    ollama pull qwen2.5:0.5b && \
    echo "Model qwen2.5:0.5b cached successfully into image layer." && \
    kill -9 $BUILD_PID 2>/dev/null || true

# Copy source code and entrypoint
COPY . .

# Convert line endings and make entrypoint executable
RUN sed -i 's/\r$//' entrypoint.sh 2>/dev/null || true && \
    chmod +x entrypoint.sh start.py 2>/dev/null || true

# Runtime configuration
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OLLAMA_MODEL=qwen2.5:0.5b \
    PORT=8000 \
    HOST=0.0.0.0

EXPOSE 8000 11434

HEALTHCHECK --interval=20s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
