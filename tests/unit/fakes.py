from __future__ import annotations

from datetime import UTC, datetime

from merlin.ai.memory.models import MemoryMessage
from merlin.ai.memory.store import MemoryStore
from merlin.ai.models.request import MessageRole


class FakeMemoryStore(MemoryStore):
    """MemoryStore in-memory para tests: sin I/O real, estado en un dict."""

    def __init__(self) -> None:
        self._messages: dict[str, list[MemoryMessage]] = {}

    async def append(self, session_id: str, role: MessageRole, content: str) -> None:
        self._messages.setdefault(session_id, []).append(
            MemoryMessage(
                session_id=session_id,
                role=role,
                content=content,
                created_at=datetime.now(UTC),
            )
        )

    async def get_recent(self, session_id: str, limit: int) -> list[MemoryMessage]:
        return self._messages.get(session_id, [])[-limit:]
