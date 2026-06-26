"""
backend/app/infrastructure/chat_repository.py
Supabase-backed message storage using the `messages` table.

Table schema (messages):
  id         BIGSERIAL PRIMARY KEY
  student_id BIGINT / TEXT   NOT NULL
  role       TEXT            NOT NULL  -- 'user' | 'assistant'
  content    TEXT            NOT NULL
  created_at TIMESTAMPTZ     DEFAULT now()

CHANGED: Table renamed from chat_messages → messages (per spec).
         All functions are async using asyncio.to_thread() to wrap
         the synchronous supabase-py client without blocking the event loop.
"""

import asyncio
from datetime import datetime, timezone
from typing import Union

from app.config.supabase_client import supabase

TABLE = "messages"


async def insert_message(
    student_id: Union[int, str],
    role: str,
    content: str,
) -> dict:
    """
    Persist a single chat message.
    role must be 'user' or 'assistant'.
    Returns the inserted row dict.
    """
    def _insert():
        return (
            supabase.table(TABLE)
            .insert({
                "student_id": student_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            .execute()
        )

    result = await asyncio.to_thread(_insert)
    return result.data[0] if result.data else {}


async def get_recent_messages(
    student_id: Union[int, str],
    limit: int = 10,
) -> list[dict]:
    """
    Return the last `limit` messages for a student in chronological order.
    Fetches DESC (newest first) then reverses for correct display order.
    Enforces a hard cap of 10 to protect LLM context windows.
    """
    cap = min(limit, 10)

    def _query():
        return (
            supabase.table(TABLE)
            .select("id, student_id, role, content, created_at")
            .eq("student_id", student_id)
            .order("created_at", desc=True)
            .limit(cap)
            .execute()
        )

    result = await asyncio.to_thread(_query)
    rows = result.data or []
    return list(reversed(rows))
