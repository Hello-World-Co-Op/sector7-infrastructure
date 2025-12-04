"""
Aurora Forester - Database Connection Utilities
PostgreSQL connection pool and query helpers for Aurora's persistence layer.
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
import os
import json
from datetime import datetime

# Note: These imports require asyncpg package
# import asyncpg
# from asyncpg import Pool, Connection


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "aurora-postgres.aurora-system.svc.cluster.local"
    port: int = 5432
    database: str = "aurora"
    user: str = "aurora_agent"
    password: str = ""
    min_connections: int = 2
    max_connections: int = 10

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.environ.get("AURORA_DB_HOST", cls.host),
            port=int(os.environ.get("AURORA_DB_PORT", cls.port)),
            database=os.environ.get("AURORA_DB_NAME", cls.database),
            user=os.environ.get("AURORA_DB_USER", cls.user),
            password=os.environ.get("AURORA_DB_PASSWORD", ""),
            min_connections=int(os.environ.get("AURORA_DB_MIN_CONN", cls.min_connections)),
            max_connections=int(os.environ.get("AURORA_DB_MAX_CONN", cls.max_connections)),
        )


class AuroraDatabase:
    """
    Aurora's database connection manager.
    Provides connection pooling and query helpers.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self._pool = None

    async def connect(self):
        """Initialize the connection pool."""
        # Placeholder - requires asyncpg
        # self._pool = await asyncpg.create_pool(
        #     host=self.config.host,
        #     port=self.config.port,
        #     database=self.config.database,
        #     user=self.config.user,
        #     password=self.config.password,
        #     min_size=self.config.min_connections,
        #     max_size=self.config.max_connections,
        # )
        pass

    async def close(self):
        """Close all connections in the pool."""
        if self._pool:
            # await self._pool.close()
            pass

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        # Placeholder
        # async with self._pool.acquire() as conn:
        #     yield conn
        yield None

    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status."""
        # async with self.acquire() as conn:
        #     return await conn.execute(query, *args)
        return "OK"

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and fetch all results."""
        # async with self.acquire() as conn:
        #     rows = await conn.fetch(query, *args)
        #     return [dict(row) for row in rows]
        return []

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query and fetch one result."""
        # async with self.acquire() as conn:
        #     row = await conn.fetchrow(query, *args)
        #     return dict(row) if row else None
        return None

    async def fetchval(self, query: str, *args) -> Any:
        """Execute a query and fetch a single value."""
        # async with self.acquire() as conn:
        #     return await conn.fetchval(query, *args)
        return None


# ============================================
# REPOSITORY CLASSES
# ============================================

class ConversationRepository:
    """Repository for conversation and message operations."""

    def __init__(self, db: AuroraDatabase):
        self.db = db

    async def create_conversation(
        self,
        session_id: str,
        channel: str,
        channel_id: Optional[str] = None
    ) -> str:
        """Create a new conversation and return its ID."""
        query = """
            INSERT INTO aurora_core.conversations (session_id, channel, channel_id)
            VALUES ($1, $2, $3)
            RETURNING id
        """
        result = await self.db.fetchval(query, session_id, channel, channel_id)
        return str(result) if result else ""

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to a conversation."""
        query = """
            INSERT INTO aurora_core.messages
            (conversation_id, role, content, embedding, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        result = await self.db.fetchval(
            query,
            conversation_id,
            role,
            content,
            embedding,
            json.dumps(metadata or {})
        )
        return str(result) if result else ""

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation."""
        query = """
            SELECT id, role, content, metadata, created_at
            FROM aurora_core.messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT $2
        """
        return await self.db.fetch(query, conversation_id, limit)

    async def search_similar_messages(
        self,
        embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar messages using vector similarity."""
        query = """
            SELECT m.id, m.content, m.role, c.channel,
                   1 - (m.embedding <=> $1) as similarity
            FROM aurora_core.messages m
            JOIN aurora_core.conversations c ON m.conversation_id = c.id
            WHERE m.embedding IS NOT NULL
            AND 1 - (m.embedding <=> $1) > $3
            ORDER BY m.embedding <=> $1
            LIMIT $2
        """
        return await self.db.fetch(query, embedding, limit, threshold)

    async def end_conversation(
        self,
        conversation_id: str,
        summary: Optional[str] = None
    ):
        """Mark a conversation as ended."""
        query = """
            UPDATE aurora_core.conversations
            SET ended_at = NOW(), summary = $2
            WHERE id = $1
        """
        await self.db.execute(query, conversation_id, summary)


class TaskRepository:
    """Repository for task and project operations."""

    def __init__(self, db: AuroraDatabase):
        self.db = db

    async def create_task(
        self,
        title: str,
        project_code: str = "personal",
        description: Optional[str] = None,
        priority: int = 5,
        due_date: Optional[datetime] = None
    ) -> str:
        """Create a new task."""
        query = """
            INSERT INTO aurora_tasks.tasks
            (title, description, priority, due_date, project_id)
            VALUES ($1, $2, $3, $4,
                (SELECT id FROM aurora_tasks.projects WHERE code = $5))
            RETURNING id
        """
        result = await self.db.fetchval(
            query, title, description, priority, due_date, project_code
        )
        return str(result) if result else ""

    async def get_active_tasks(
        self,
        project_code: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get active tasks, optionally filtered by project."""
        if project_code:
            query = """
                SELECT * FROM aurora_tasks.active_tasks
                WHERE project_code = $1
                LIMIT $2
            """
            return await self.db.fetch(query, project_code, limit)
        else:
            query = """
                SELECT * FROM aurora_tasks.active_tasks
                LIMIT $1
            """
            return await self.db.fetch(query, limit)

    async def update_task_status(self, task_id: str, status: str):
        """Update a task's status."""
        query = """
            UPDATE aurora_tasks.tasks
            SET status = $2, updated_at = NOW()
            WHERE id = $1
        """
        if status == "completed":
            query = """
                UPDATE aurora_tasks.tasks
                SET status = $2, completed_at = NOW(), updated_at = NOW()
                WHERE id = $1
            """
        await self.db.execute(query, task_id, status)

    async def get_tasks_by_priority(self, max_priority: int = 3) -> List[Dict[str, Any]]:
        """Get high-priority tasks."""
        query = """
            SELECT * FROM aurora_tasks.active_tasks
            WHERE priority <= $1
            ORDER BY priority ASC, due_date ASC NULLS LAST
        """
        return await self.db.fetch(query, max_priority)


class LearningRepository:
    """Repository for learning and pattern operations."""

    def __init__(self, db: AuroraDatabase):
        self.db = db

    async def record_observation(
        self,
        observation_type: str,
        content: str,
        confidence: float = 0.5,
        source_conversation_id: Optional[str] = None
    ) -> str:
        """Record an observation Aurora makes."""
        query = """
            INSERT INTO aurora_learning.observations
            (observation_type, content, confidence, source_conversation_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        result = await self.db.fetchval(
            query, observation_type, content, confidence, source_conversation_id
        )
        return str(result) if result else ""

    async def get_unvalidated_observations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get observations awaiting founder validation."""
        query = """
            SELECT * FROM aurora_learning.observations
            WHERE validated = FALSE
            ORDER BY confidence DESC
            LIMIT $1
        """
        return await self.db.fetch(query, limit)

    async def validate_observation(self, observation_id: str, validated: bool):
        """Mark an observation as validated (or rejected)."""
        query = """
            UPDATE aurora_learning.observations
            SET validated = $2
            WHERE id = $1
        """
        await self.db.execute(query, observation_id, validated)

    async def record_pattern(
        self,
        pattern_type: str,
        name: str,
        description: str,
        frequency: str = "situational",
        triggers: Optional[List[str]] = None
    ) -> str:
        """Record a behavioral pattern."""
        query = """
            INSERT INTO aurora_learning.patterns
            (pattern_type, name, description, frequency, triggers)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """
        result = await self.db.fetchval(
            query, pattern_type, name, description, frequency,
            json.dumps(triggers or [])
        )
        return str(result) if result else ""

    async def get_patterns_for_context(
        self,
        pattern_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get patterns for context injection."""
        if pattern_types:
            query = """
                SELECT * FROM aurora_learning.patterns
                WHERE pattern_type = ANY($1)
                ORDER BY last_observed DESC NULLS LAST
            """
            return await self.db.fetch(query, pattern_types)
        else:
            query = """
                SELECT * FROM aurora_learning.patterns
                ORDER BY last_observed DESC NULLS LAST
                LIMIT 20
            """
            return await self.db.fetch(query)


class ContextRepository:
    """Repository for RAG context library operations."""

    def __init__(self, db: AuroraDatabase):
        self.db = db

    async def add_document(
        self,
        source: str,
        content: str,
        title: Optional[str] = None,
        doc_type: str = "general",
        embedding: Optional[List[float]] = None,
        is_private: bool = False,
        tags: Optional[List[str]] = None
    ) -> str:
        """Add a document to the context library."""
        query = """
            INSERT INTO aurora_context.documents
            (source, title, content, doc_type, embedding, is_private, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        result = await self.db.fetchval(
            query, source, title, content, doc_type, embedding,
            is_private, json.dumps(tags or [])
        )
        return str(result) if result else ""

    async def search_documents(
        self,
        embedding: List[float],
        limit: int = 5,
        doc_types: Optional[List[str]] = None,
        include_private: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents using vector similarity."""
        if doc_types:
            query = """
                SELECT id, title, content, doc_type, source,
                       1 - (embedding <=> $1) as relevance
                FROM aurora_context.documents
                WHERE embedding IS NOT NULL
                AND doc_type = ANY($3)
                AND (is_private = FALSE OR $4 = TRUE)
                ORDER BY embedding <=> $1
                LIMIT $2
            """
            return await self.db.fetch(query, embedding, limit, doc_types, include_private)
        else:
            query = """
                SELECT id, title, content, doc_type, source,
                       1 - (embedding <=> $1) as relevance
                FROM aurora_context.documents
                WHERE embedding IS NOT NULL
                AND (is_private = FALSE OR $3 = TRUE)
                ORDER BY embedding <=> $1
                LIMIT $2
            """
            return await self.db.fetch(query, embedding, limit, include_private)

    async def get_documents_by_type(
        self,
        doc_type: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get documents of a specific type."""
        query = """
            SELECT id, title, content, source, tags, created_at
            FROM aurora_context.documents
            WHERE doc_type = $1
            ORDER BY updated_at DESC
            LIMIT $2
        """
        return await self.db.fetch(query, doc_type, limit)


# ============================================
# SINGLETON AND INITIALIZATION
# ============================================

_database: Optional[AuroraDatabase] = None
_conversation_repo: Optional[ConversationRepository] = None
_task_repo: Optional[TaskRepository] = None
_learning_repo: Optional[LearningRepository] = None
_context_repo: Optional[ContextRepository] = None


async def init_database(config: Optional[DatabaseConfig] = None) -> AuroraDatabase:
    """Initialize the database connection."""
    global _database
    if _database is None:
        _database = AuroraDatabase(config)
        await _database.connect()
    return _database


def get_database() -> AuroraDatabase:
    """Get the database instance (must be initialized first)."""
    global _database
    if _database is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _database


def get_conversation_repo() -> ConversationRepository:
    """Get the conversation repository."""
    global _conversation_repo
    if _conversation_repo is None:
        _conversation_repo = ConversationRepository(get_database())
    return _conversation_repo


def get_task_repo() -> TaskRepository:
    """Get the task repository."""
    global _task_repo
    if _task_repo is None:
        _task_repo = TaskRepository(get_database())
    return _task_repo


def get_learning_repo() -> LearningRepository:
    """Get the learning repository."""
    global _learning_repo
    if _learning_repo is None:
        _learning_repo = LearningRepository(get_database())
    return _learning_repo


def get_context_repo() -> ContextRepository:
    """Get the context repository."""
    global _context_repo
    if _context_repo is None:
        _context_repo = ContextRepository(get_database())
    return _context_repo
