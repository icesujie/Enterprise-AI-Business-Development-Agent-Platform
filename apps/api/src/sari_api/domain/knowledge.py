from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExtractedSection:
    text: str
    page_number: int | None = None
    section_title: str | None = None


@dataclass(frozen=True, slots=True)
class TextChunk:
    index: int
    text: str
    page_number: int | None
    section_title: str | None


def normalize_extracted_text(value: str) -> str:
    value = value.replace("\x00", " ").replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def chunk_sections(
    sections: list[ExtractedSection],
    *,
    chunk_size: int,
    overlap: int,
) -> list[TextChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunking limits.")
    chunks: list[TextChunk] = []
    for section in sections:
        text = normalize_extracted_text(section.text)
        if not text:
            continue
        start = 0
        while start < len(text):
            hard_end = min(start + chunk_size, len(text))
            end = hard_end
            if hard_end < len(text):
                paragraph_break = text.rfind("\n\n", start + chunk_size // 2, hard_end)
                sentence_break = max(
                    text.rfind(". ", start + chunk_size // 2, hard_end),
                    text.rfind("。", start + chunk_size // 2, hard_end),
                )
                if paragraph_break > start:
                    end = paragraph_break
                elif sentence_break > start:
                    end = sentence_break + 1
            value = text[start:end].strip()
            if value:
                chunks.append(
                    TextChunk(
                        index=len(chunks),
                        text=value,
                        page_number=section.page_number,
                        section_title=section.section_title,
                    )
                )
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
    return chunks
