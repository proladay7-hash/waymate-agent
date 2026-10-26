#!/usr/bin/env bash
set -e

echo "=================================================================="
echo "          Starting WayMate AI Agent Container                     "
echo "=================================================================="

# Determine whether to use external or embedded Ollama
USE_EMBEDDED_OLLAMA=true
if [ -n "$OLLAMA_HOST" ] && [[ "$OLLAMA_HOST" != *"localhost"* ]] && [[ "$OLLAMA_HOST" != *"127.0.0.1"* ]] && [[ "$OLLAMA_HOST" != *"0.0.0.0"* ]]; then
    echo "Connecting to external Ollama host: $OLLAMA_HOST"
    USE_EMBEDDED_OLLAMA=false
fi

if [ "$USE_EMBEDDED_OLLAMA" = true ]; then
    echo "Starting embedded Ollama daemon on port 11434..."
    OLLAMA_HOST=0.0.0.0:11434 ollama serve > /app/ollama_daemon.log 2>&1 &
    OLLAMA_PID=$!

    echo "Waiting for Ollama daemon to initialize..."
    for i in {1..30}; do
        if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
            echo "Embedded Ollama is ready."
            break
        fi
        sleep 1
    done

    # Verify model is available; pull if volume override or missing
    TARGET_MODEL="${OLLAMA_MODEL:-qwen2.5:0.5b}"
    if ! ollama list | grep -q "${TARGET_MODEL%:*}"; then
        echo "Model $TARGET_MODEL not found locally, pulling..."
        ollama pull "$TARGET_MODEL"
    else
        echo "Model $TARGET_MODEL is verified and ready in embedded Ollama."
    fi
fi

# Initialize knowledge base if not already present
if [ -f "build_waymate_knowledge.py" ] && [ ! -f "scraped_website.json" ]; then
    echo "Populating initial WayMate knowledge..."
    python build_waymate_knowledge.py || true
fi

echo "Starting WayMate AI Agent service..."
exec python start.py
