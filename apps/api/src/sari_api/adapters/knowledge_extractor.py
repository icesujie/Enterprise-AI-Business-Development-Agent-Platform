from __future__ import annotations

import asyncio
from io import BytesIO
from typing import Protocol

from pypdf import PdfReader

from sari_api.domain.knowledge import ExtractedSection, normalize_extracted_text


class UnsupportedKnowledgeDocumentError(Exception):
    pass


class EmptyKnowledgeDocumentError(Exception):
    pass


class KnowledgeTextExtractor(Protocol):
    async def extract(self, content: bytes, media_type: str) -> list[ExtractedSection]: ...


class DefaultKnowledgeTextExtractor:
    supported_media_types = frozenset(
        {
            "application/pdf",
            "text/plain",
            "text/markdown",
            "text/x-markdown",
        }
    )

    async def extract(self, content: bytes, media_type: str) -> list[ExtractedSection]:
        normalized_type = media_type.split(";", maxsplit=1)[0].strip().lower()
        if normalized_type not in self.supported_media_types:
            raise UnsupportedKnowledgeDocumentError
        if normalized_type == "application/pdf":
            sections = await asyncio.to_thread(self._extract_pdf, content)
        else:
            sections = self._extract_text(content)
        if not any(section.text.strip() for section in sections):
            raise EmptyKnowledgeDocumentError
        return sections

    @staticmethod
    def _extract_text(content: bytes) -> list[ExtractedSection]:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsupportedKnowledgeDocumentError from exc
        return [ExtractedSection(text=normalize_extracted_text(text))]

    @staticmethod
    def _extract_pdf(content: bytes) -> list[ExtractedSection]:
        try:
            reader = PdfReader(BytesIO(content))
            return [
                ExtractedSection(
                    text=normalize_extracted_text(page.extract_text() or ""),
                    page_number=index,
                )
                for index, page in enumerate(reader.pages, start=1)
            ]
        except Exception as exc:
            raise UnsupportedKnowledgeDocumentError from exc
