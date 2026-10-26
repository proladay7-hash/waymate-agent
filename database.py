import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

try:
    import aiosqlite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "./ai_agent.db"):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
        
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def initialize(self):
        """Initialize the database and create tables"""
        def _init_sync():
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT,
                        user_message TEXT NOT NULL,
                        ai_response TEXT NOT NULL,
                        sources TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        session_id TEXT,
                        user_id TEXT,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_base_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action TEXT NOT NULL,
                        document_url TEXT,
                        document_title TEXT,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        try:
            await asyncio.to_thread(_init_sync)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def log_conversation(
        self, 
        session_id: str, 
        user_id: Optional[str], 
        user_message: str, 
        ai_response: str, 
        sources: List[Dict[str, Any]] = None
    ):
        """Log a conversation exchange"""
        def _log_sync():
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO conversations (session_id, user_id, user_message, ai_response, sources)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    user_message,
                    ai_response,
                    json.dumps(sources) if sources else None
                ))
                conn.commit()
        try:
            await asyncio.to_thread(_log_sync)
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
    
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        def _get_history_sync():
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM conversations 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (session_id, limit))
                rows = cursor.fetchall()
                conversations = []
                for row in rows:
                    conversations.append({
                        "id": row["id"],
                        "session_id": row["session_id"],
                        "user_id": row["user_id"],
                        "user_message": row["user_message"],
                        "ai_response": row["ai_response"],
                        "sources": json.loads(row["sources"]) if row["sources"] else [],
                        "created_at": row["created_at"]
                    })
                return conversations
        try:
            return await asyncio.to_thread(_get_history_sync)
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def log_analytics_event(
        self, 
        event_type: str, 
        session_id: Optional[str] = None, 
        user_id: Optional[str] = None, 
        data: Dict[str, Any] = None
    ):
        """Log an analytics event"""
        def _log_event_sync():
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO analytics (event_type, session_id, user_id, data)
                    VALUES (?, ?, ?, ?)
                """, (
                    event_type,
                    session_id,
                    user_id,
                    json.dumps(data) if data else None
                ))
                conn.commit()
        try:
            await asyncio.to_thread(_log_event_sync)
        except Exception as e:
            logger.error(f"Error logging analytics event: {e}")
    
    async def close(self):
        """Close database connections"""
        pass