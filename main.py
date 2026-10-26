from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
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

class SuppressUpgradeWarningsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "Unsupported upgrade request" in msg or "Invalid HTTP request received" in msg:
            return False
        return True

for uvicorn_log in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logging.getLogger(uvicorn_log).addFilter(SuppressUpgradeWarningsFilter())


app = FastAPI(
    title="WayMate AI Agent",
    description="AI-powered assistant for WayMate adventure travel, motorcycle community & vehicle maintenance tracker",
    version="2.0.0"
)

# CORS middleware - Allow all origins for mobile, Expo web, and dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
chat_manager = ChatManager()
ollama_client = OllamaClient()
website_scraper = WebsiteScraper(base_url=settings.website_base_url)
db_manager = DatabaseManager()

# Pydantic models (flexible to accept any schema)
class ChatMessage(BaseModel):
    message: Optional[str] = None
    prompt: Optional[str] = None
    content: Optional[str] = None
    text: Optional[str] = None
    query: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    user_id: Optional[Any] = None
    session_id: Optional[Any] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    sources: List[Dict[str, Any]] = []

@app.on_event("startup")
async def startup_event():
    """Initialize the WayMate AI agent on startup"""
    logger.info("Starting WayMate AI Agent...")
    try:
        await db_manager.initialize()
    except Exception as e:
        logger.warning(f"Database init warning (non-critical): {e}")

    # Ensure knowledge base is populated
    if not website_scraper.scraped_data:
        website_scraper.load_data()
    logger.info(f"WayMate AI Agent started successfully with {len(website_scraper.scraped_data)} knowledge items!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down WayMate AI Agent...")
    try:
        await db_manager.close()
    except Exception:
        pass

@app.websocket("/ws/chat")
@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """WebSocket endpoint for real-time chat with WayMate AI Agent"""
    active_session = session_id or str(uuid.uuid4())
    await chat_manager.connect(websocket, active_session)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            user_id = message_data.get("user_id")
            
            if user_message.strip():
                response = await generate_ai_response(user_message, session_id, user_id)
                
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "message": response.response,
                    "session_id": session_id,
                    "timestamp": response.timestamp.isoformat(),
                    "sources": response.sources
                }))
                
                try:
                    await db_manager.log_conversation(
                        session_id=session_id,
                        user_id=user_id,
                        user_message=user_message,
                        ai_response=response.response,
                        sources=response.sources
                    )
                except Exception as log_err:
                    logger.debug(f"DB log note: {log_err}")
    
    except WebSocketDisconnect:
        chat_manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        chat_manager.disconnect(session_id)
        logger.warning(f"WebSocket exception for session {session_id}: {e}")

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """REST API endpoint for WayMate chat.
    Accepts all standard payload formats (message, prompt, content, query, text, or messages array).
    Guarantees no 422 Unprocessable Entity validation errors.
    """
    try:
        try:
            body = await request.json()
        except Exception:
            raw_text = (await request.body()).decode("utf-8", errors="ignore").strip()
            body = {"message": raw_text} if raw_text else {}

        if not isinstance(body, dict):
            body = {"message": str(body)}

        # Extract message from any possible field name
        message_str = (
            body.get("message")
            or body.get("prompt")
            or body.get("content")
            or body.get("text")
            or body.get("query")
        )

        # Handle OpenAI / Ollama style messages array: [{"role": "user", "content": "..."}]
        if not message_str and "messages" in body and isinstance(body["messages"], list):
            for m in reversed(body["messages"]):
                if isinstance(m, dict) and m.get("content"):
                    message_str = m.get("content")
                    break

        if not message_str or not str(message_str).strip():
            message_str = "Xin chào WayMate AI Agent"

        user_text = str(message_str).strip()
        session_id = str(body.get("session_id") or uuid.uuid4())
        user_id = str(body.get("user_id") or "waymate_rider")

        logger.info(f"[/api/chat] Processing prompt from user '{user_id}': {user_text}")

        response = await generate_ai_response(user_text, session_id, user_id)
        return {
            "response": response.response,
            "session_id": response.session_id,
            "timestamp": response.timestamp.isoformat() if hasattr(response.timestamp, "isoformat") else str(response.timestamp),
            "sources": response.sources or []
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return {
            "response": "🤖 [WayMate AI Agent]: Xin chào! Tôi là trợ lý ảo WayMate. Bạn cần tư vấn về cung đường phượt hay bảo dưỡng xe máy/ô tô?",
            "session_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "sources": []
        }

@app.get("/api/health")
async def health_check():
    """Health check endpoint with Ollama status"""
    ollama_ok = await ollama_client.check_health()
    return {
        "status": "healthy",
        "app": "WayMate AI Agent",
        "timestamp": datetime.now().isoformat(),
        "ollama_status": ollama_ok,
        "mode": "ollama_active" if ollama_ok else "agent_offline",
        "knowledge_entries": len(website_scraper.scraped_data)
    }

@app.get("/health")
async def root_health():
    return {"status": "ok", "app": "WayMate AI Agent"}

@app.post("/api/learn-waymate")
@app.get("/api/learn-waymate")
async def learn_waymate_endpoint():
    """Endpoint to trigger re-indexing/learning of all WayMate client knowledge"""
    try:
        website_scraper.refresh_from_client()
        return {
            "status": "success",
            "message": f"WayMate knowledge base updated successfully with {len(website_scraper.scraped_data)} entries.",
            "entries_count": len(website_scraper.scraped_data)
        }
    except Exception as e:
        logger.error(f"Error learning WayMate knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge-base/stats")
async def knowledge_base_stats():
    """Get knowledge base statistics"""
    categories = {}
    types = {}
    for entry in website_scraper.scraped_data:
        meta = entry.get("metadata", {})
        cat = meta.get("category", "general")
        typ = meta.get("type", "page")
        categories[cat] = categories.get(cat, 0) + 1
        types[typ] = types.get(typ, 0) + 1

    return {
        "total_documents": len(website_scraper.scraped_data),
        "categories": categories,
        "types": types,
        "timestamp": datetime.now().isoformat()
    }

async def generate_ai_response(message: str, session_id: str, user_id: Optional[str] = None) -> ChatResponse:
    """Generate AI response using Ollama qwen2.5:0.5b"""
    try:
        history = await chat_manager.get_conversation_history(session_id)
        relevant_docs = website_scraper.search(message, max_results=4)
        context = create_context_from_documents(relevant_docs)

        ai_response = await ollama_client.generate_response(
            message=message,
            context=context,
            history=history
        )

        await chat_manager.add_message(session_id, "user", message)
        await chat_manager.add_message(session_id, "assistant", ai_response)

        sources = []
        for doc in relevant_docs:
            title = doc.get("title", "")
            url = doc.get("url", "")
            if title:
                sources.append({"title": title, "url": url})

        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            timestamp=datetime.now(),
            sources=sources[:3]
        )
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return ChatResponse(
            response="WayMate AI Agent is currently not available. Please ensure Ollama is running with model qwen2.5:0.5b.",
            session_id=session_id,
            timestamp=datetime.now()
        )

def create_context_from_documents(documents: List[Dict[str, Any]]) -> str:
    """Create clean context string from relevant WayMate documents"""
    if not documents:
        return ""
    
    context_parts = []
    for doc in documents:
        title = doc.get("title", "")
        content = doc.get("content", "")
        context_parts.append(f"[{title}]\n{content}\n")
    
    return "\n".join(context_parts)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)