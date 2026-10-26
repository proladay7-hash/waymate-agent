import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    app_name: str = "WayMate AI Agent"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:0.5b"
    ollama_timeout: int = 60
    
    # Knowledge base settings
    knowledge_base_path: str = "./knowledge_base"
    max_search_results: int = 5
    
    # Database settings
    database_path: str = "./ai_agent.db"
    
    # Website & Service settings
    website_base_url: str = "http://localhost:8782"
    backend_api_url: str = "http://localhost:8781"
    scraping_timeout: int = 10
    max_concurrent_scrapes: int = 5
    
    # Chat settings
    max_conversation_history: int = 20
    session_timeout_hours: int = 24
    
    # CORS settings - Allows Expo Web, Metro bundler, React Native, Vite and local ports
    allowed_origins: List[str] = [
        "*",
        "http://localhost:8782",
        "http://127.0.0.1:8782",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:19006",
        "http://localhost:8000",
    ]
    
    # Logging settings
    log_level: str = "INFO"
    
    # Security settings
    api_key_header: str = "X-API-Key"
    api_key: Optional[str] = None
    
    # AI Model settings
    anthropic_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    # Demo mode settings
    demo_mode: bool = False
    
    # Environment variables
    database_url: Optional[str] = None
    chroma_persist_directory: str = "./knowledge_base"
    embedding_model: str = "text-embedding-ada-002"
    scraping_delay: int = 1
    max_retries: int = 3
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()
