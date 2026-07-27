from __future__ import annotations

from pathlib import Path

from merlin.ai.memory.sqlite_store import SqliteMemoryStore
from merlin.ai.models.request import MessageRole


async def test_append_and_get_recent_roundtrip(tmp_path: Path) -> None:
    store = SqliteMemoryStore(db_path=tmp_path / "memory.db")

    await store.append("s1", MessageRole.USER, "Hola")
    await store.append("s1", MessageRole.ASSISTANT, "¡Hola! ¿En qué te ayudo?")

    messages = await store.get_recent("s1", limit=10)

    assert [m.content for m in messages] == ["Hola", "¡Hola! ¿En qué te ayudo?"]
    assert [m.role for m in messages] == [MessageRole.USER, MessageRole.ASSISTANT]


async def test_get_recent_respects_limit_and_chronological_order(tmp_path: Path) -> None:
    store = SqliteMemoryStore(db_path=tmp_path / "memory.db")

    for i in range(5):
        await store.append("s1", MessageRole.USER, f"mensaje {i}")

    messages = await store.get_recent("s1", limit=2)

    assert [m.content for m in messages] == ["mensaje 3", "mensaje 4"]


async def test_sessions_are_isolated(tmp_path: Path) -> None:
    store = SqliteMemoryStore(db_path=tmp_path / "memory.db")

    await store.append("session-a", MessageRole.USER, "solo A")
    await store.append("session-b", MessageRole.USER, "solo B")

    messages_a = await store.get_recent("session-a", limit=10)

    assert [m.content for m in messages_a] == ["solo A"]


async def test_store_persists_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "memory.db"

    store1 = SqliteMemoryStore(db_path=db_path)
    await store1.append("s1", MessageRole.USER, "mensaje persistente")

    store2 = SqliteMemoryStore(db_path=db_path)
    messages = await store2.get_recent("s1", limit=10)

    assert [m.content for m in messages] == ["mensaje persistente"]
