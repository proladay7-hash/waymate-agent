#!/usr/bin/env python3
"""
WayMate AI Agent Startup Script
Initializes and runs the WayMate AI agent with proper error handling and logging.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from ollama_client import OllamaClient
from website_scraper import WebsiteScraper
from database import DatabaseManager
from config import settings
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_agent.log', encoding='utf-8')
    ]
)

class SuppressUpgradeWarningsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "Unsupported upgrade request" in msg or "Invalid HTTP request received" in msg:
            return False
        return True

for uvicorn_log in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logging.getLogger(uvicorn_log).addFilter(SuppressUpgradeWarningsFilter())

logger = logging.getLogger(__name__)

async def check_ollama():
    """Check if Ollama is running"""
    try:
        client = OllamaClient()
        is_healthy = await client.check_health()
        
        if is_healthy:
            logger.info(f"Ollama is running and model {client.model_name} is ready.")
        else:
            logger.warning(f"Ollama is not running locally or model {client.model_name} is not loaded.")
            logger.warning(f"If queries fail, start Ollama and ensure {client.model_name} is available.")
        return True
    except Exception as e:
        logger.warning(f"Ollama check note: {e}")
        return True

async def initialize_database():
    """Initialize the database"""
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("Database initialized successfully.")
        return True
    except Exception as e:
        logger.warning(f"Database initialization note: {e}")
        return True

def print_banner():
    """Print startup banner"""
    banner = f"""
    ================================================================
                         WayMate AI Agent                           
                                                                    
      Model: {settings.ollama_model} | WayMate Dedicated Assistant   
      Real-time AI Chatbot for Adventure Travel & Routes           
      Vehicle Garage & Maintenance Tracking (3,000km/5,000km)      
      WebSocket and REST API for Expo / React Native               
    ================================================================
    """
    print(banner)

async def main_init():
    """Main startup initialization"""
    print_banner()
    logger.info("Starting WayMate AI Agent...")
    await check_ollama()
    await initialize_database()
    
    # Verify knowledge base
    scraper = WebsiteScraper()
    logger.info(f"Loaded {len(scraper.scraped_data)} WayMate knowledge entries.")
    
    logger.info("All systems ready!")
    logger.info(f"AI Agent listening at: http://{settings.host}:{settings.port}")
    logger.info(f"REST Chat endpoint: http://{settings.host}:{settings.port}/api/chat")
    logger.info(f"WebSocket endpoint: ws://{settings.host}:{settings.port}/ws/chat/{{session_id}}")
    logger.info(f"Learn WayMate endpoint: http://{settings.host}:{settings.port}/api/learn-waymate")
    logger.info("Press Ctrl+C to stop the server.")

if __name__ == "__main__":
    try:
        asyncio.run(main_init())
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("AI Agent stopped by user")
    except Exception as e:
        logger.error(f"Failed to start AI Agent: {e}")
        sys.exit(1)