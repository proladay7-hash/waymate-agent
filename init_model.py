#!/usr/bin/env python3
"""
Model initialization script for the AI agent
This script ensures the required model is available when the container starts
"""
import os
import subprocess
import time
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_model_available(model_name="llama3.2:1b"):
    """Check if the model is already available"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            return model_name in result.stdout
    except FileNotFoundError:
        logger.error("Ollama is not installed or not in PATH")
        return False
    return False

def wait_for_ollama(max_wait=60):
    """Wait for Ollama service to be available"""
    logger.info("Waiting for Ollama service to be available...")
    
    for i in range(max_wait):
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Ollama service is available")
                return True
        except FileNotFoundError:
            pass
        
        if i < max_wait - 1:
            time.sleep(1)
    
    logger.error("Ollama service did not become available")
    return False

def main():
    """Main initialization function"""
    model_name = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
    
    logger.info(f"Initializing model: {model_name}")
    
    # Wait for Ollama to be available
    if not wait_for_ollama():
        logger.error("Failed to connect to Ollama service")
        return False
    
    # Check if model is already available
    if check_model_available(model_name):
        logger.info(f"Model {model_name} is already available")
        return True
    else:
        logger.error(f"Model {model_name} is not available locally.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 