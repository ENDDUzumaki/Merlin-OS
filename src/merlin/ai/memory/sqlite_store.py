"""Implementación de MemoryStore sobre SQLite.

Único módulo del sistema que conoce el esquema de la base de datos. Usa
sqlite3 (stdlib) en vez de una dependencia externa como aiosqlite: sqlite3
no es async-nativo, así que las operaciones se delegan a un hilo con
asyncio.to_thread para no bloquear el event loop del resto del sistema.
"""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from merlin.ai.memory.models import MemoryMessage, MessageRole
from merlin.ai.memory.store import MemoryStore

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id, id);
"""


class SqliteMemoryStore(MemoryStore):
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.executescript(_SCHEMA)

    async def append(self, session_id: str, role: MessageRole, content: str) -> None:
        await asyncio.to_thread(self._append_sync, session_id, role, content)

    def _append_sync(self, session_id: str, role: MessageRole, content: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, role.value, content, datetime.now(UTC).isoformat()),
            )

    async def get_recent(self, session_id: str, limit: int) -> list[MemoryMessage]:
        return await asyncio.to_thread(self._get_recent_sync, session_id, limit)

    def _get_recent_sync(self, session_id: str, limit: int) -> list[MemoryMessage]:
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT role, content, created_at FROM messages "
                "WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()

        messages = [
            MemoryMessage(
                session_id=session_id,
                role=MessageRole(role),
                content=content,
                created_at=datetime.fromisoformat(created_at),
            )
            for role, content, created_at in rows
        ]
        return list(reversed(messages))
