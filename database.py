import asyncio
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiosqlite
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "./ai_agent.db"):
        self.db_path = db_path
        
    async def initialize(self):
        """Initialize the database and create tables"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create conversations table
                await db.execute("""
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
                
                # Create analytics table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        session_id TEXT,
                        user_id TEXT,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create knowledge_base_logs table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_base_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action TEXT NOT NULL,
                        document_url TEXT,
                        document_title TEXT,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await db.commit()
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
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO conversations (session_id, user_id, user_message, ai_response, sources)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    user_message,
                    ai_response,
                    json.dumps(sources) if sources else None
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
    
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute("""
                    SELECT * FROM conversations 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (session_id, limit))
                
                rows = await cursor.fetchall()
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
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO analytics (event_type, session_id, user_id, data)
                    VALUES (?, ?, ?, ?)
                """, (
                    event_type,
                    session_id,
                    user_id,
                    json.dumps(data) if data else None
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error logging analytics event: {e}")
    
    async def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics summary for the specified number of days"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # Get total conversations
                cursor = await db.execute("""
                    SELECT COUNT(*) as count FROM conversations 
                    WHERE created_at >= datetime('now', '-{} days')
                """.format(days))
                total_conversations = (await cursor.fetchone())["count"]
                
                # Get unique users
                cursor = await db.execute("""
                    SELECT COUNT(DISTINCT user_id) as count FROM conversations 
                    WHERE user_id IS NOT NULL AND created_at >= datetime('now', '-{} days')
                """.format(days))
                unique_users = (await cursor.fetchone())["count"]
                
                # Get event counts
                cursor = await db.execute("""
                    SELECT event_type, COUNT(*) as count FROM analytics 
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY event_type
                """.format(days))
                events = await cursor.fetchall()
                event_counts = {row["event_type"]: row["count"] for row in events}
                
                return {
                    "period_days": days,
                    "total_conversations": total_conversations,
                    "unique_users": unique_users,
                    "event_counts": event_counts
                }
                
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {}
    
    async def log_knowledge_base_action(
        self, 
        action: str, 
        document_url: Optional[str] = None, 
        document_title: Optional[str] = None, 
        status: str = "success"
    ):
        """Log knowledge base actions"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO knowledge_base_logs (action, document_url, document_title, status)
                    VALUES (?, ?, ?, ?)
                """, (action, document_url, document_title, status))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error logging knowledge base action: {e}")
    
    async def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular user queries"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute("""
                    SELECT user_message, COUNT(*) as count 
                    FROM conversations 
                    GROUP BY user_message 
                    ORDER BY count DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = await cursor.fetchall()
                return [{"query": row["user_message"], "count": row["count"]} for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting popular queries: {e}")
            return []
    
    async def search_conversations(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search conversations by content"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute("""
                    SELECT * FROM conversations 
                    WHERE user_message LIKE ? OR ai_response LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                rows = await cursor.fetchall()
                conversations = []
                
                for row in rows:
                    conversations.append({
                        "id": row["id"],
                        "session_id": row["session_id"],
                        "user_id": row["user_id"],
                        "user_message": row["user_message"],
                        "ai_response": row["ai_response"],
                        "created_at": row["created_at"]
                    })
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return []
    
    async def close(self):
        """Close database connections"""
        # aiosqlite handles connection closing automatically
        pass
    
    async def backup_database(self, backup_path: str):
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data from the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Clean up old conversations
                await db.execute("""
                    DELETE FROM conversations 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days))
                
                # Clean up old analytics
                await db.execute("""
                    DELETE FROM analytics 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days))
                
                # Clean up old knowledge base logs
                await db.execute("""
                    DELETE FROM knowledge_base_logs 
                    WHERE created_at < datetime('now', '-{} days')
                """.format(days))
                
                await db.commit()
                logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}") 