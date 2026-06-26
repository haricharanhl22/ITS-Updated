"""
backend/app/application/tutor_service.py
AI tutor service with RAG retrieval + Groq LLM.

ARCHITECTURE:
  1. Embed question with SentenceTransformer all-MiniLM-L6-v2
  2. Retrieve top-5 chunks from textbook_chunks via pgvector
  3. Detect concept from retrieved chunks (or keyword fallback)
  4. Fetch student mastery for that concept
  5. Fetch last 5 messages for conversation context
  6. Build adaptive prompt (mastery-aware, per spec)
  7. Call Groq API (llama-3.3-70b-versatile) — falls back to template stub
  8. Persist both messages; return answer + cited chunks

Prompt follows the exact spec template:
  - mastery < 0.4  → simple language + analogies
  - mastery 0.4-0.7 → moderate detail with examples
  - mastery > 0.7  → advanced and concise
  - Always encouraging, suggests quiz if mastery < 0.6
"""
from __future__ import annotations

import asyncio
import logging
import re
import random
from dataclasses import dataclass, field
from typing import Optional

from app.config.settings import settings
from app.config.supabase_client import supabase
from app.infrastructure import chat_repository
from app.rag.retrieval import RetrievedChunk, retrieve

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Concept keyword map
# ---------------------------------------------------------------------------

CONCEPT_KEYWORDS: dict[str, list[str]] = {
    "Functions":      ["def", "function", "lambda", "return", "argument", "parameter", "decorator", "docstring"],
    "OOP":            ["class", "object", "polymorphism", "inheritance", "encapsulation", "method", "self", "instance", "dunder"],
    "Variables":      ["variable", "assign", "int", "str", "float", "type", "constant", "scope", "name"],
    "Loops":          ["loop", "for", "while", "iterate", "range", "break", "continue", "enumerate", "comprehension"],
    "Strings":        ["string", "concatenation", "slice", "strip", "format", "f-string", "upper", "lower", "split", "join"],
    "Lists":          ["list", "append", "index", "sort", "pop", "extend", "element"],
    "Dictionaries":   ["dict", "dictionary", "key", "value", "json", "hashmap", "get", "items", "keys", "values"],
    "Error Handling": ["try", "except", "raise", "exception", "error", "finally", "traceback", "valueerror"],
}

_CONTINUATION_WORDS = {
    "then", "more", "next", "continue", "go", "on", "elaborate",
    "example", "examples", "show", "another", "again", "how", "why",
    "ok", "okay", "got", "it", "yes", "yep", "yeah", "sure", "so",
    "interesting", "and", "what", "else", "please", "can", "you",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TutorContext:
    question: str
    student_id: int | str
    concept: str
    mastery_score: float
    retrieved_chunks: list[RetrievedChunk]
    recent_messages: list[dict]


# ---------------------------------------------------------------------------
# Concept detection helpers
# ---------------------------------------------------------------------------

def _detect_concept_from_text(text: str) -> str:
    """Word-boundary keyword match. Returns 'General' if no concept found."""
    q_lower = text.lower()
    best, best_count = "General", 0
    for concept, kws in CONCEPT_KEYWORDS.items():
        count = sum(1 for kw in kws if re.search(r"\b" + re.escape(kw) + r"\b", q_lower))
        if count > best_count:
            best_count = count
            best = concept
    return best


def _detect_concept_from_chunks(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "General"
    combined = " ".join(c.content for c in chunks[:3])
    return _detect_concept_from_text(combined)


def _is_continuation(question: str) -> bool:
    words = question.lower().strip().rstrip("?!.,").split()
    return len(words) <= 3 and all(w in _CONTINUATION_WORDS for w in words)


# ---------------------------------------------------------------------------
# Mastery fetch
# ---------------------------------------------------------------------------

def _get_mastery_sync(student_id: int | str, concept: str) -> float:
    try:
        res = (
            supabase.table("student_mastery")
            .select("mastery_score")
            .eq("student_id", student_id)
            .eq("concept_name", concept)
            .limit(1)
            .execute()
        )
        if res.data:
            return float(res.data[0].get("mastery_score") or 0.0)
    except Exception as e:
        logger.warning(f"Mastery fetch failed: {e}")
    return 0.0


# ---------------------------------------------------------------------------
# Prompt builder (spec-compliant)
# ---------------------------------------------------------------------------

def _build_prompt(ctx: TutorContext) -> str:
    """
    Build the adaptive system + user prompt following the exact spec template:

    You are a Python tutor. Adapt your explanation based on the student's mastery level.
    Student Mastery: {concept_name}: {mastery_score}/1.0
    Relevant Textbook Content: {chunk_1} {chunk_2} {chunk_3}
    Recent Conversation: {last_5_messages}
    Student Question: {current_question}

    Instructions:
    - mastery < 0.4 → simple language + analogies
    - mastery 0.4-0.7 → moderate detail with examples
    - mastery > 0.7 → advanced and concise
    - Always encouraging, suggest quiz if mastery < 0.6
    """
    mastery = ctx.mastery_score
    concept = ctx.concept
    chunks  = ctx.retrieved_chunks

    # Determine tone instruction
    if mastery < 0.4:
        tone = (
            "Use very simple language with real-world analogies. "
            "Break down every concept step by step as if explaining to a complete beginner. "
            "Include a concrete code example. "
            "At the end, gently suggest taking a quiz on this topic to build confidence."
        )
    elif mastery <= 0.7:
        tone = (
            "Use moderate detail with well-commented code examples. "
            "The student knows the basics — challenge them a little and introduce nuances. "
            "If mastery is below 0.6, suggest a quiz at the end."
        )
    else:
        tone = (
            "Be advanced and concise. Skip the basics. Discuss edge cases, best practices, "
            "and Pythonic patterns. The student has strong mastery — treat them as a peer."
        )

    # Build chunk context (top 3 per spec)
    chunk_texts = []
    for i, chunk in enumerate(chunks[:3], 1):
        excerpt = chunk.content[:600].strip()
        chunk_texts.append(f"[Chunk {i} — page {chunk.page_number}]:\n{excerpt}")
    chunks_section = "\n\n".join(chunk_texts) if chunk_texts else "No textbook content retrieved."

    # Build conversation history (last 5 messages per spec)
    history_lines = []
    for msg in ctx.recent_messages[-5:]:
        role_label = "Student" if msg.get("role") == "user" else "Tutor"
        history_lines.append(f"{role_label}: {msg.get('content', '')[:200]}")
    history_section = "\n".join(history_lines) if history_lines else "No prior conversation."

    system_prompt = (
        f"You are an expert Python tutor. Adapt your explanation based on the student's mastery level.\n"
        f"Always be encouraging and supportive.\n\n"
        f"Student Mastery — {concept}: {mastery:.2f}/1.0\n\n"
        f"Tone instructions: {tone}\n\n"
        f"Relevant Textbook Content:\n{chunks_section}\n\n"
        f"Recent Conversation:\n{history_section}"
    )

    user_prompt = f"Student Question: {ctx.question}"

    return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# Groq LLM call
# ---------------------------------------------------------------------------

def _call_groq_sync(system_prompt: str, user_prompt: str) -> str:
    """
    Call the Groq API synchronously (will be run in a thread).
    Uses the model from settings (default: llama-3.3-70b-versatile).
    Raises RuntimeError if GROQ_API_KEY is not configured.
    """
    from groq import Groq

    api_key = settings.groq_api_key
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    client = Groq(api_key=api_key)

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=1024,
        top_p=0.9,
    )

    return completion.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Template fallback (when Groq key not configured)
# ---------------------------------------------------------------------------

def _template_response(ctx: TutorContext) -> str:
    """Intelligent template response — used when GROQ_API_KEY is absent."""
    mastery  = ctx.mastery_score
    concept  = ctx.concept
    chunks   = ctx.retrieved_chunks
    q_lower  = ctx.question.lower()

    openers_beginner     = ["Great question! Let's break this down step by step.",
                             "That's a really good point. Let's look closer.",
                             "I'm glad you asked! Here is how we can think about it."]
    openers_intermediate = [f"Good question. You already know the basics of **{concept}** — let's go deeper.",
                             "Nice! Let's expand on what you already know.",
                             "You're on the right track. Let's refine your understanding."]
    openers_advanced     = [f"Solid question. You're well into **{concept}** — here's a more nuanced view.",
                             "Excellent question for an advanced learner. Let's look at the details.",
                             "You've grasped the core concepts well, so let's tackle this edge case."]

    if mastery < 0.35:
        opener = random.choice(openers_beginner)
    elif mastery < 0.65:
        opener = random.choice(openers_intermediate)
    else:
        opener = random.choice(openers_advanced)

    if chunks:
        lines = [l for l in chunks[0].content.split("\n") if l.strip() and not l.startswith("#")]
        excerpt = "\n".join(lines[:12]).strip()
        if len(excerpt) > 800:
            excerpt = excerpt[:800].rsplit(" ", 1)[0] + "..."
        explanation = f"Regarding your question about **{ctx.question}**, here is the relevant material:\n\n{excerpt}"
    else:
        explanation = (
            f"I see you're asking about **{ctx.question}**. "
            f"This relates to **{concept}**. "
            f"Please upload a textbook PDF so I can give you a more precise answer from the course material."
        )

    suffix = ""
    if mastery < 0.6:
        suffix = f"\n\n💡 **Tip:** Take the **{concept}** quiz to strengthen your understanding!"

    return f"{opener}\n\n{explanation}{suffix}"


# ---------------------------------------------------------------------------
# Main LLM entry point
# ---------------------------------------------------------------------------

async def generate_groq_response(ctx: TutorContext) -> str:
    """
    Try Groq API first; fall back to template on error or missing key.
    """
    if not settings.groq_api_key:
        logger.info("GROQ_API_KEY not set — using template fallback.")
        return _template_response(ctx)

    try:
        system_prompt, user_prompt = _build_prompt(ctx)
        answer = await asyncio.to_thread(_call_groq_sync, system_prompt, user_prompt)
        logger.info(f"Groq response received ({len(answer)} chars) for concept '{ctx.concept}'")
        return answer
    except Exception as e:
        logger.warning(f"Groq API call failed ({e}), using template fallback.")
        return _template_response(ctx)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def get_answer(question: str, student_id: str) -> dict:
    """
    Full RAG pipeline:
      embed -> retrieve -> detect concept -> fetch mastery -> build context -> generate
    Returns: { answer, concept_detected, cited_chunks, mastery_before }
    """
    sid: int | str = int(student_id) if str(student_id).isdigit() else student_id

    # 1. Retrieve relevant chunks (top-5 per spec)
    chunks = await retrieve(question, match_count=5, match_threshold=0.30)

    # 2. Detect concept
    concept_from_chunks   = _detect_concept_from_chunks(chunks)
    concept_from_question = _detect_concept_from_text(question)

    if concept_from_chunks != "General":
        concept = concept_from_chunks
    elif concept_from_question != "General":
        concept = concept_from_question
    elif _is_continuation(question):
        concept = await _get_last_concept(sid) or "General"
    else:
        concept = "General"

    # 3. Fetch mastery
    mastery_before = await asyncio.to_thread(_get_mastery_sync, sid, concept)

    # 4. Fetch recent conversation history (last 5 per spec)
    recent = await chat_repository.get_recent_messages(sid, limit=5)

    # 5. Build context and generate response
    ctx = TutorContext(
        question=question,
        student_id=sid,
        concept=concept,
        mastery_score=mastery_before,
        retrieved_chunks=chunks,
        recent_messages=recent,
    )
    answer = await generate_groq_response(ctx)

    # 6. Persist messages (best-effort)
    try:
        await chat_repository.insert_message(sid, "user", question)
        await chat_repository.insert_message(sid, "assistant", answer)
    except Exception as e:
        logger.warning(f"Message persistence failed: {e}")

    # 7. Format cited chunks for the frontend (top-3 per spec)
    cited = [
        {
            "id":          c.id,
            "excerpt":     c.excerpt(250),
            "similarity":  round(c.similarity, 3),
            "page_number": c.page_number,
        }
        for c in chunks[:3]
    ]

    return {
        "answer":           answer,
        "concept_detected": concept,
        "cited_chunks":     cited,
        "mastery_before":   mastery_before,
    }


async def _get_last_concept(student_id: int | str) -> Optional[str]:
    """Look at last 5 assistant messages to find recently active concept."""
    def _query():
        return (
            supabase.table("messages")
            .select("content")
            .eq("student_id", student_id)
            .eq("role", "assistant")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
    try:
        result = await asyncio.to_thread(_query)
        for row in result.data or []:
            c = _detect_concept_from_text(row.get("content", ""))
            if c != "General":
                return c
    except Exception:
        pass
    return None
