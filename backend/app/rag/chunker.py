"""
backend/app/rag/chunker.py
Splits markdown text into overlapping chunks of ~300-500 tokens.
Uses simple word-based splitting with sentence boundary awareness.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class TextChunk:
    content: str
    page_number: int    # maps to lesson file index
    chunk_index: int    # position within the file
    concept: str        # derived from filename


# Approximate tokens per word for English text
_WORDS_PER_TOKEN = 0.75
_TARGET_TOKENS = 400
_OVERLAP_TOKENS = 80
_TARGET_WORDS = int(_TARGET_TOKENS / _WORDS_PER_TOKEN)    # ~533 words
_OVERLAP_WORDS = int(_OVERLAP_TOKENS / _WORDS_PER_TOKEN)  # ~107 words


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentence-ish units preserving code blocks."""
    # Preserve code blocks as single units
    code_block_pattern = r"```[\s\S]*?```"
    code_blocks = {}
    counter = [0]

    def replace_code(m: re.Match) -> str:
        key = f"__CODE_{counter[0]}__"
        code_blocks[key] = m.group(0)
        counter[0] += 1
        return key

    clean = re.sub(code_block_pattern, replace_code, text)

    # Split on double newlines (paragraph boundaries) and sentence endings
    parts = re.split(r"\n{2,}|(?<=[.!?])\s+", clean)
    result = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Restore code blocks
        for key, block in code_blocks.items():
            part = part.replace(key, block)
        result.append(part)
    return result


def chunk_text(text: str, page_number: int, concept: str) -> list[TextChunk]:
    """
    Split text into overlapping chunks.
    Each chunk is ~300-500 tokens with ~80-token overlap.
    """
    sentences = _split_into_sentences(text)
    if not sentences:
        return []

    chunks: list[TextChunk] = []
    chunk_idx = 0
    current_words: list[str] = []
    current_sentences: list[str] = []

    for sent in sentences:
        sent_words = sent.split()
        current_words.extend(sent_words)
        current_sentences.append(sent)

        if len(current_words) >= _TARGET_WORDS:
            chunk_text_str = "\n\n".join(current_sentences).strip()
            if chunk_text_str:
                chunks.append(TextChunk(
                    content=chunk_text_str,
                    page_number=page_number,
                    chunk_index=chunk_idx,
                    concept=concept,
                ))
                chunk_idx += 1

            # Carry forward overlap: last N words worth of sentences
            overlap_sentences: list[str] = []
            overlap_words = 0
            for s in reversed(current_sentences):
                w = len(s.split())
                if overlap_words + w > _OVERLAP_WORDS:
                    break
                overlap_sentences.insert(0, s)
                overlap_words += w

            current_sentences = overlap_sentences
            current_words = " ".join(current_sentences).split()

    # Emit remaining text as the final chunk
    if current_sentences:
        chunk_text_str = "\n\n".join(current_sentences).strip()
        if chunk_text_str and len(current_words) > 20:
            chunks.append(TextChunk(
                content=chunk_text_str,
                page_number=page_number,
                chunk_index=chunk_idx,
                concept=concept,
            ))

    return chunks


def chunk_file(filepath: Path, page_number: int) -> list[TextChunk]:
    """Read a markdown file and return its chunks."""
    text = filepath.read_text(encoding="utf-8")
    # Derive concept from filename (e.g., variables.md → Variables)
    concept = filepath.stem.replace("_", " ").title()
    return chunk_text(text, page_number, concept)


def chunk_directory(directory: Path) -> Iterator[TextChunk]:
    """Yield all chunks from all .md files in a directory."""
    md_files = sorted(directory.glob("*.md"))
    for page_num, filepath in enumerate(md_files, start=1):
        yield from chunk_file(filepath, page_num)
