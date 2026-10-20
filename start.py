#!/usr/bin/env python3
"""
BigBikeBlitz AI Agent Startup Script
Initializes and runs the AI agent with proper error handling and logging.
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
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_agent.log')
    ]
)

logger = logging.getLogger(__name__)

async def check_ollama():
    """Check if Ollama is running and Mistral 7B is available"""
    try:
        client = OllamaClient()
        is_healthy = await client.check_health()
        
        if not is_healthy:
            logger.error("❌ Ollama is not running or Llama 3.2 1B model is not available")
            logger.info("Please ensure:")
            logger.info("1. Ollama is installed and running: ollama serve")
            return True
        
        model_info = await client.get_model_info()
        logger.info(f"✅ Ollama is running with model: {model_info.get('name', 'Unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Ollama: {e}")
        return False

async def initialize_database():
    """Initialize the database"""
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        return False



async def scrape_website_if_needed():
    """Scrape website if knowledge base is empty"""
    try:
        logger.info("🌐 Starting website scraping...")
        # scraper = WebsiteScraper(base_url="https://bigbikeblitz-production.up.railway.app")
        scraper = WebsiteScraper(base_url="http://localhost:5173")
        
        # Scrape main pages
        pages = [
            "http://localhost:5173",
            "http://localhost:5173/categories",
            "http://localhost:5173/about",
            "http://localhost:5173/contact",
            "http://localhost:5173/help"
        ]
        
        for page in pages:
            try:
                data = await scraper.scrape_page(page)
                if data:
                    # Note: kb.add_document is not available in this context
                    # The scraping is handled by the main.py startup event
                    logger.info(f"✅ Scraped: {page}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to scrape {page}: {e}")
        
        logger.info("✅ Website scraping completed")
            
    except Exception as e:
        logger.error(f"❌ Failed to scrape website: {e}")

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    BigBikeBlitz AI Agent                     ║
    ║                                                              ║
    ║  🚀 Powered by Llama 3.2 1B via Ollama                        ║
    ║  🤖 Real-time AI chat for motorcycle e-commerce             ║
    ║  📚 Intelligent knowledge base with website scraping        ║
    ║  🔗 WebSocket and REST API support                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Main startup function"""
    print_banner()
    
    logger.info("🚀 Starting BigBikeBlitz AI Agent...")
    
    # Check prerequisites
    logger.info("🔍 Checking prerequisites...")
    
    # Check Ollama
    if not await check_ollama():
        logger.error("❌ Cannot start without Ollama. Please fix the issues above.")
        sys.exit(1)
    
    # Initialize database
    if not await initialize_database():
        logger.error("❌ Cannot start without database. Please fix the issues above.")
        sys.exit(1)
    
    # Scrape website if needed
    await scrape_website_if_needed()
    
    logger.info("✅ All systems ready!")
    logger.info("🌐 AI Agent will be available at: http://localhost:8000")
    logger.info("📖 API Documentation: http://localhost:8000/docs")
    logger.info("🔌 WebSocket endpoint: ws://localhost:8000/ws/chat/{session_id}")
    logger.info("")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("=" * 60)

if __name__ == "__main__":
    try:
        # Run startup checks
        asyncio.run(main())
        
        # Start the FastAPI server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 AI Agent stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start AI Agent: {e}")
        sys.exit(1) 