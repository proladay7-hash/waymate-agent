import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ChatManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        # Initialize conversation history for this session
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        logger.info(f"Client connected: {session_id}")
        
        # Send welcome message
        welcome_message = {
            "type": "system",
            "message": "Welcome to BigBikeBlitz AI Assistant! I'm here to help you find the perfect motorcycle and answer any questions about our services.",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(welcome_message))
    
    def disconnect(self, session_id: str):
        """Disconnect a WebSocket client"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"Client disconnected: {session_id}")
    
    async def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_history[session_id].append(message)
        
        # Keep only last 20 messages to prevent memory issues
        if len(self.conversation_history[session_id]) > 20:
            self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        if session_id not in self.conversation_history:
            return []
        
        # Return only user and assistant messages (exclude system messages)
        messages = []
        for msg in self.conversation_history[session_id]:
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return messages
    
    async def broadcast_message(self, message: str, exclude_session: str = None):
        """Broadcast a message to all connected clients"""
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            if session_id != exclude_session:
                try:
                    await websocket.send_text(json.dumps({
                        "type": "broadcast",
                        "message": message,
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error broadcasting to {session_id}: {e}")
                    disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            self.disconnect(session_id)
    
    async def send_to_user(self, session_id: str, message: Dict[str, Any]):
        """Send a message to a specific user"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.active_connections.keys())
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_connections)
    
    async def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        
        if user_id:
            self.user_sessions[user_id] = session_id
        
        self.conversation_history[session_id] = []
        
        logger.info(f"Created new session: {session_id} for user: {user_id}")
        return session_id
    
    async def get_session_by_user(self, user_id: str) -> Optional[str]:
        """Get session ID for a user"""
        return self.user_sessions.get(user_id)
    
    async def end_session(self, session_id: str):
        """End a chat session"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].close()
            self.disconnect(session_id)
        
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
        
        # Remove from user sessions
        user_id_to_remove = None
        for user_id, sid in self.user_sessions.items():
            if sid == session_id:
                user_id_to_remove = user_id
                break
        
        if user_id_to_remove:
            del self.user_sessions[user_id_to_remove]
        
        logger.info(f"Ended session: {session_id}")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions"""
        return {
            "active_sessions": self.get_session_count(),
            "total_conversations": len(self.conversation_history),
            "connected_users": len(self.user_sessions)
        }
    
    async def clear_old_sessions(self, max_age_hours: int = 24):
        """Clear old conversation history"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        sessions_to_remove = []
        
        for session_id, messages in self.conversation_history.items():
            if messages:
                # Check if last message is older than cutoff
                last_message_time = datetime.fromisoformat(messages[-1]["timestamp"]).timestamp()
                if last_message_time < cutoff_time:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            if session_id not in self.active_connections:  # Only remove inactive sessions
                del self.conversation_history[session_id]
                logger.info(f"Cleared old session: {session_id}")
    
    async def export_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export conversation history for a session"""
        if session_id not in self.conversation_history:
            return None
        
        return {
            "session_id": session_id,
            "messages": self.conversation_history[session_id],
            "exported_at": datetime.now().isoformat()
        } 