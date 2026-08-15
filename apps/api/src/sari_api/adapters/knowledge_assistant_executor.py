from __future__ import annotations

import logging
import math
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_assistant_provider import KnowledgeAssistantProvider
from sari_api.adapters.knowledge_assistant_repository import KnowledgeAssistantRepository
from sari_api.adapters.knowledge_embedding import KnowledgeEmbeddingProvider
from sari_api.adapters.managed_knowledge_retrieval import (
    ManagedKnowledgeRetrievalDeniedError,
    ManagedKnowledgeRetrievalRepository,
    ManagedKnowledgeSearchHit,
)
from sari_api.adapters.qualification_executor import RetrySchedule
from sari_api.core.config import Settings
from sari_api.domain.knowledge_assistant import (
    KnowledgeAssistantEvidence,
    KnowledgeAssistantLanguage,
    KnowledgeAssistantResult,
    conflicting_result,
    detect_evidence_conflicts,
    insufficient_result,
    validate_knowledge_assistant_draft,
)

logger = logging.getLogger(__name__)


class KnowledgeAssistantRunExecutor:
    def __init__(
        self,
        embedding_provider: KnowledgeEmbeddingProvider,
        answer_provider: KnowledgeAssistantProvider,
        settings: Settings,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._answer_provider = answer_provider
        self._settings = settings

    async def execute(self, run_id: UUID, tenant_id: UUID) -> RetrySchedule | None:
        started = time.perf_counter()
        async with session_factory() as session:
            runs = KnowledgeAssistantRepository(session, tenant_id)
            await runs.set_tenant_context()
            run = await runs.get_run(run_id, for_update=True)
            if run.status != "queued":
                return None
            if run.next_retry_at and run.next_retry_at > datetime.now(UTC):
                remaining = math.ceil((run.next_retry_at - datetime.now(UTC)).total_seconds())
                return RetrySchedule(max(remaining, 1), run.correlation_id)
            snapshot = run.input_snapshot
            agent_id = UUID(str(snapshot["agent_id"]))
            language = _language(snapshot.get("language"))
            question = str(snapshot.get("question", "")).strip()
            retrieval = ManagedKnowledgeRetrievalRepository(session, tenant_id)
            await retrieval.set_tenant_context()
            try:
                context = await retrieval.get_agent_retrieval_context(agent_id)
            except ManagedKnowledgeRetrievalDeniedError:
                await runs.fail_run(
                    run,
                    "agent_access_denied",
                    "Knowledge Assistant access is no longer enabled for this agent.",
                )
                await session.commit()
                return None
            if (
                context.domain_key != "commercial_kitchen"
                or context.agent_key != "commercial_kitchen.lead_qualification"
            ):
                await runs.fail_run(
                    run,
                    "agent_access_denied",
                    "Knowledge Assistant is enabled only for the Commercial Kitchen Agent.",
                )
                await session.commit()
                return None
            await runs.start_run(run)
            attempt_count = run.attempt_count
            max_attempts = run.max_attempts
            await session.commit()

        try:
            query_embedding = (await self._embedding_provider.embed([question]))[0]
            async with session_factory() as session:
                retrieval = ManagedKnowledgeRetrievalRepository(session, tenant_id)
                await retrieval.set_tenant_context()
                hits = await retrieval.search(
                    agent_id=agent_id,
                    query_embedding=query_embedding,
                    embedding_provider=self._embedding_provider.provider_type,
                    embedding_model=self._embedding_provider.model_id,
                    language=language,
                    top_k=self._settings.knowledge_assistant_top_k,
                    minimum_similarity=self._settings.knowledge_retrieval_min_similarity,
                )
            evidence = [_evidence(hit) for hit in hits]
            if len(evidence) < self._settings.knowledge_retrieval_min_evidence_count:
                result = insufficient_result(language, evidence)
            else:
                conflict_keys = detect_evidence_conflicts(evidence)
                if conflict_keys:
                    result = conflicting_result(language, evidence, conflict_keys)
                else:
                    draft = await self._answer_provider.answer(question, language, evidence)
                    citations = validate_knowledge_assistant_draft(draft, language, evidence)
                    result = KnowledgeAssistantResult(
                        evidence_status="sufficient",
                        answer=draft.answer,
                        citations=citations,
                        evidence=evidence,
                        retrieved_result_count=len(evidence),
                        model_provider=self._answer_provider.provider_type,
                        model_id=self._answer_provider.model_id,
                    )
        except ManagedKnowledgeRetrievalDeniedError:
            await self._fail_access(run_id, tenant_id)
            return None
        except Exception:
            logger.exception(
                "Knowledge Assistant execution failed",
                extra={
                    "event": "knowledge_assistant.run.attempt_failed",
                    "agent_run_id": str(run_id),
                    "tenant_id": str(tenant_id),
                    "agent_id": str(agent_id),
                    "language": language,
                    "attempt_count": attempt_count,
                    "max_attempts": max_attempts,
                },
            )
            return await self._handle_failure(
                run_id,
                tenant_id,
                attempt_count,
                max_attempts,
                run.correlation_id,
            )

        async with session_factory() as session:
            runs = KnowledgeAssistantRepository(session, tenant_id)
            await runs.set_tenant_context()
            current = await runs.get_run(run_id, for_update=True)
            if current.status != "running":
                return None
            await runs.complete_run(current, result)
            await session.commit()
        logger.info(
            "Knowledge Assistant run completed",
            extra={
                "event": "knowledge_assistant.run.completed",
                "agent_run_id": str(run_id),
                "tenant_id": str(tenant_id),
                "agent_id": str(agent_id),
                "language": language,
                "result_count": result.retrieved_result_count,
                "provider_type": result.model_provider,
                "model_id": result.model_id,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "outcome": result.evidence_status,
            },
        )
        return None

    async def _fail_access(self, run_id: UUID, tenant_id: UUID) -> None:
        async with session_factory() as session:
            runs = KnowledgeAssistantRepository(session, tenant_id)
            await runs.set_tenant_context()
            run = await runs.get_run(run_id, for_update=True)
            if run.status == "running":
                await runs.fail_run(
                    run,
                    "agent_access_denied",
                    "Knowledge Assistant access was revoked before retrieval completed.",
                )
                await session.commit()

    async def _handle_failure(
        self,
        run_id: UUID,
        tenant_id: UUID,
        attempt_count: int,
        max_attempts: int,
        correlation_id: str | None,
    ) -> RetrySchedule | None:
        async with session_factory() as session:
            runs = KnowledgeAssistantRepository(session, tenant_id)
            await runs.set_tenant_context()
            run = await runs.get_run(run_id, for_update=True)
            if run.status != "running":
                return None
            if attempt_count < max_attempts:
                delay = self._settings.agent_retry_base_seconds * (2 ** (attempt_count - 1))
                await runs.schedule_retry(
                    run,
                    "assistant_temporarily_unavailable",
                    "Knowledge Assistant is temporarily unavailable. Automatic retry scheduled.",
                    delay,
                )
                await session.commit()
                return RetrySchedule(delay, correlation_id)
            await runs.fail_run(
                run,
                "assistant_unavailable",
                "Knowledge Assistant is unavailable after bounded retries.",
            )
            await session.commit()
        return None

    async def fail_scheduled_retry(self, run_id: UUID, tenant_id: UUID) -> None:
        async with session_factory() as session:
            runs = KnowledgeAssistantRepository(session, tenant_id)
            await runs.set_tenant_context()
            run = await runs.get_run(run_id, for_update=True)
            if run.status == "queued":
                await runs.fail_run(
                    run,
                    "queue_unavailable",
                    "Knowledge Assistant retry could not be queued.",
                )
                await session.commit()


def _evidence(hit: ManagedKnowledgeSearchHit) -> KnowledgeAssistantEvidence:
    similarity = round(max(-1.0, min(1.0, 1.0 - float(hit.distance))), 6)
    chunk = hit.chunk
    document = hit.document
    version = hit.version
    metadata = {
        **chunk.source_metadata,
        "document_type": chunk.document_type,
        "language": chunk.language,
        "chunk_index": chunk.chunk_index,
    }
    return KnowledgeAssistantEvidence(
        document_id=document.id,
        document_name=document.title,
        document_version_id=version.id,
        document_version=version.version_number,
        page_number=chunk.page_number,
        section=chunk.section_title,
        chunk_id=chunk.id,
        source_metadata=metadata,
        similarity_score=similarity,
        content=chunk.content,
        content_sha256=chunk.content_sha256,
    )


def _language(value: Any) -> KnowledgeAssistantLanguage:
    if value == "en":
        return "en"
    if value == "zh-CN":
        return "zh-CN"
    raise ValueError("Unsupported Knowledge Assistant language.")
