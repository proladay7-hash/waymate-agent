from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio
import logging
from datetime import datetime
import uuid

from chat_manager import ChatManager
from ollama_client import OllamaClient
from website_scraper import WebsiteScraper
from database import DatabaseManager
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BigBikeBlitz AI Agent",
    description="AI-powered chatbot for BigBikeBlitz motorcycle e-commerce website",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://bigbikeblitz-production.up.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
chat_manager = ChatManager()
ollama_client = OllamaClient()
website_scraper = WebsiteScraper(base_url="http://localhost:5173")
db_manager = DatabaseManager()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    sources: List[Dict[str, Any]] = []

class WebsiteData(BaseModel):
    url: str
    content: str
    metadata: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize the AI agent on startup"""
    logger.info("Starting BigBikeBlitz AI Agent...")
    await db_manager.initialize()
    # Scrape website data if not already available
    if not website_scraper.scraped_data:
        website_scraper.scrape_urls()
    logger.info("AI Agent started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Agent...")
    await db_manager.close()

@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await chat_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            user_message = message_data.get("message", "")
            user_id = message_data.get("user_id")
            
            if user_message.strip():
                # Generate AI response
                response = await generate_ai_response(user_message, session_id, user_id)
                
                # Send response back to client
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "message": response.response,
                    "session_id": session_id,
                    "timestamp": response.timestamp.isoformat(),
                    "sources": response.sources
                }))
                
                # Log conversation
                await db_manager.log_conversation(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=user_message,
                    ai_response=response.response,
                    sources=response.sources
                )
    
    except WebSocketDisconnect:
        chat_manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """REST API endpoint for chat"""
    try:
        response = await generate_ai_response(
            chat_message.message, 
            chat_message.session_id or str(uuid.uuid4()),
            chat_message.user_id
        )
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ollama_status": await ollama_client.check_health(),
    }

@app.get("/health")
async def root_health():
    return {"status": "ok"}

async def generate_ai_response(message: str, session_id: str, user_id: Optional[str] = None) -> ChatResponse:
    """Generate AI response using Mistral 7B"""
    try:
        # Get conversation history
        history = await chat_manager.get_conversation_history(session_id)
        # Search website data for relevant information
        relevant_docs = website_scraper.search(message, max_results=5)
        # Create context from relevant documents
        context = create_context_from_documents(relevant_docs)
        # Generate response using Ollama
        ai_response = await ollama_client.generate_response(
            message=message,
            context=context,
            history=history
        )
        # Update conversation history
        await chat_manager.add_message(session_id, "user", message)
        await chat_manager.add_message(session_id, "assistant", ai_response)
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            timestamp=datetime.now(),
            sources=[{"title": doc.get("title", ""), "url": doc.get("url", "")} for doc in relevant_docs]
        )
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return ChatResponse(
            response="I apologize, but I'm having trouble processing your request right now. Please try again later.",
            session_id=session_id,
            timestamp=datetime.now()
        )

def create_context_from_documents(documents: List[Dict[str, Any]]) -> str:
    """Create context string from relevant documents"""
    if not documents:
        return ""
    
    context_parts = []
    for doc in documents:
        title = doc.get("title", "")
        content = doc.get("content", "")
        url = doc.get("url", "")
        doc_type = doc.get("metadata", {}).get("type", "page")
        
        if doc_type == "product":
            # For products, include specific details
            brand = doc.get("metadata", {}).get("brand", "")
            model = doc.get("metadata", {}).get("model", "")
            price = doc.get("metadata", {}).get("price", "")
            engine = doc.get("metadata", {}).get("engine_size", "")
            horsepower = doc.get("metadata", {}).get("horsepower", "")
            
            context_parts.append(f"Product: {brand} {model}\nPrice: {price}\nEngine: {engine}\nHorsepower: {horsepower}\nDetails: {content}\n")
        else:
            context_parts.append(f"Title: {title}\nURL: {url}\nContent: {content}\n")
    
    return "\n".join(context_parts)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 