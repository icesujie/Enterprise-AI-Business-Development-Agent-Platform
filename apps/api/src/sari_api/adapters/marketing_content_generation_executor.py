from __future__ import annotations

import logging
import math
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sari_api.adapters.database import session_factory
from sari_api.adapters.knowledge_embedding import KnowledgeEmbeddingProvider
from sari_api.adapters.managed_knowledge_retrieval import (
    ManagedKnowledgeRetrievalDeniedError,
    ManagedKnowledgeRetrievalRepository,
    ManagedKnowledgeSearchHit,
)
from sari_api.adapters.marketing_content_generation_repository import (
    MarketingContentGenerationRepository,
)
from sari_api.adapters.marketing_content_provider import MarketingContentProvider
from sari_api.adapters.qualification_executor import RetrySchedule
from sari_api.core.config import Settings
from sari_api.domain.knowledge_assistant import detect_evidence_conflicts
from sari_api.domain.marketing_content_generation import (
    MarketingEvidence,
    contains_forbidden_request,
    validate_draft,
)

logger = logging.getLogger(__name__)


class MarketingContentGenerationExecutor:
    def __init__(
        self,
        embedding_provider: KnowledgeEmbeddingProvider,
        generation_provider: MarketingContentProvider,
        settings: Settings,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._generation_provider = generation_provider
        self._settings = settings

    async def execute(self, run_id: UUID, tenant_id: UUID) -> RetrySchedule | None:
        started = time.perf_counter()
        async with session_factory() as session:
            repo = MarketingContentGenerationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run, generation, request = await repo.get_run(run_id, lock=True)
            if run.status != "queued":
                return None
            if run.next_retry_at and run.next_retry_at > datetime.now(UTC):
                return RetrySchedule(
                    max(math.ceil((run.next_retry_at - datetime.now(UTC)).total_seconds()), 1),
                    run.correlation_id,
                )
            retrieval = ManagedKnowledgeRetrievalRepository(session, tenant_id)
            await retrieval.set_tenant_context()
            try:
                context = await retrieval.get_marketing_generation_context(generation.agent_id)
            except ManagedKnowledgeRetrievalDeniedError:
                await repo.fail(
                    run,
                    generation,
                    request,
                    "marketing_access_denied",
                    "Marketing generation is not enabled for this tenant agent.",
                )
                await session.commit()
                return None
            if context.domain_id != request.domain_id or request.agent_id != generation.agent_id:
                await repo.fail(
                    run,
                    generation,
                    request,
                    "marketing_scope_mismatch",
                    "Marketing request scope does not match the enabled agent.",
                )
                await session.commit()
                return None
            await repo.start(run, request)
            attempt = run.attempt_count
            max_attempts = run.max_attempts
            request_data = _request_data(request)
            await session.commit()

        try:
            forbidden = contains_forbidden_request(
                str(request_data["topic"]),
                str(request_data["business_objective"]),
                str(request_data["constraints"]),
            )
            evidence: list[MarketingEvidence] = []
            evidence_status = "insufficient"
            if not forbidden:
                query = "\n".join(
                    str(request_data[key]) for key in ("topic", "business_objective", "audience")
                )
                query_embedding = (await self._embedding_provider.embed([query]))[0]
                async with session_factory() as session:
                    retrieval = ManagedKnowledgeRetrievalRepository(session, tenant_id)
                    await retrieval.set_tenant_context()
                    hits = await retrieval.search(
                        agent_id=UUID(str(request_data["agent_id"])),
                        query_embedding=query_embedding,
                        embedding_provider=self._embedding_provider.provider_type,
                        embedding_model=self._embedding_provider.model_id,
                        language=str(request_data["language"]),
                        top_k=self._settings.marketing_content_top_k,
                        minimum_similarity=self._settings.knowledge_retrieval_min_similarity,
                    )
                evidence = [_evidence(item) for item in hits]
                if len(evidence) >= self._settings.knowledge_retrieval_min_evidence_count:
                    conflict_keys = detect_evidence_conflicts(
                        [_assistant_evidence(item) for item in evidence]
                    )
                    evidence_status = "conflicting" if conflict_keys else "sufficient"
            citations = [_citation(item) for item in evidence]
            duration = round((time.perf_counter() - started) * 1000)
            if forbidden or evidence_status != "sufficient":
                async with session_factory() as session:
                    repo = MarketingContentGenerationRepository(session, tenant_id)
                    await repo.set_tenant_context()
                    current, generation, request = await repo.get_run(run_id, lock=True)
                    if current.status == "running":
                        await repo.complete_insufficient(
                            current,
                            generation,
                            request,
                            evidence_status=evidence_status,
                            citations=citations,
                            provider=self._generation_provider.provider_type,
                            model=self._generation_provider.model_id,
                            duration_ms=duration,
                        )
                        await session.commit()
                logger.info(
                    "Marketing content run completed without draft",
                    extra={
                        "event": "marketing_content.run.completed",
                        "correlation_id": run.correlation_id,
                        "tenant_id": str(tenant_id),
                        "agent_id": str(request_data["agent_id"]),
                        "capability": "public_marketing_content_generation",
                        "evidence_status": evidence_status,
                        "retrieved_result_count": len(evidence),
                        "provider_type": self._generation_provider.provider_type,
                        "model_id": self._generation_provider.model_id,
                        "duration_ms": duration,
                        "outcome": "insufficient_evidence",
                    },
                )
                return None
            draft = await self._generation_provider.generate(request_data, evidence)
            validated = validate_draft(draft, str(request_data["content_type"]), evidence)
            async with session_factory() as session:
                repo = MarketingContentGenerationRepository(session, tenant_id)
                await repo.set_tenant_context()
                current, generation, request = await repo.get_run(run_id, lock=True)
                if current.status == "running":
                    await repo.complete_generated(
                        current,
                        generation,
                        request,
                        draft=validated,
                        citations=citations,
                        provider=self._generation_provider.provider_type,
                        model=self._generation_provider.model_id,
                        duration_ms=round((time.perf_counter() - started) * 1000),
                    )
                    await session.commit()
            logger.info(
                "Marketing content run generated governed draft",
                extra={
                    "event": "marketing_content.run.completed",
                    "correlation_id": run.correlation_id,
                    "tenant_id": str(tenant_id),
                    "agent_id": str(request_data["agent_id"]),
                    "capability": "public_marketing_content_generation",
                    "evidence_status": evidence_status,
                    "retrieved_result_count": len(evidence),
                    "provider_type": self._generation_provider.provider_type,
                    "model_id": self._generation_provider.model_id,
                    "duration_ms": round((time.perf_counter() - started) * 1000),
                    "outcome": "generated",
                },
            )
        except ManagedKnowledgeRetrievalDeniedError:
            await self._fail(
                run_id,
                tenant_id,
                "marketing_access_denied",
                "Marketing knowledge access was revoked.",
            )
        except Exception:
            logger.exception(
                "Marketing content generation attempt failed",
                extra={
                    "event": "marketing_content.run.attempt_failed",
                    "agent_run_id": str(run_id),
                    "tenant_id": str(tenant_id),
                },
            )
            return await self._retry_or_fail(
                run_id, tenant_id, attempt, max_attempts, run.correlation_id
            )
        return None

    async def _retry_or_fail(
        self,
        run_id: UUID,
        tenant_id: UUID,
        attempt: int,
        max_attempts: int,
        correlation_id: str | None,
    ) -> RetrySchedule | None:
        async with session_factory() as session:
            repo = MarketingContentGenerationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run, generation, request = await repo.get_run(run_id, lock=True)
            if run.status != "running":
                return None
            if attempt < max_attempts:
                delay = self._settings.agent_retry_base_seconds * (2 ** (attempt - 1))
                await repo.schedule_retry(run, request, delay)
                await session.commit()
                return RetrySchedule(delay, correlation_id)
            await repo.fail(
                run,
                generation,
                request,
                "marketing_generation_failed",
                "Marketing draft generation failed after bounded retries.",
            )
            await session.commit()
        return None

    async def _fail(self, run_id: UUID, tenant_id: UUID, code: str, message: str) -> None:
        async with session_factory() as session:
            repo = MarketingContentGenerationRepository(session, tenant_id)
            await repo.set_tenant_context()
            run, generation, request = await repo.get_run(run_id, lock=True)
            if run.status == "running":
                await repo.fail(run, generation, request, code, message)
                await session.commit()

    async def fail_scheduled_retry(self, run_id: UUID, tenant_id: UUID) -> None:
        await self._fail(
            run_id,
            tenant_id,
            "queue_unavailable",
            "Marketing generation retry could not be queued.",
        )


def _request_data(request: Any) -> dict[str, object]:
    return {
        "request_id": str(request.id),
        "agent_id": str(request.agent_id),
        "content_type": request.content_type,
        "audience": request.audience,
        "language": request.language,
        "channel": request.channel,
        "business_objective": request.business_objective,
        "topic": request.topic,
        "call_to_action": request.call_to_action,
        "campaign_name": request.campaign_name,
        "constraints": request.constraints,
    }


def _evidence(hit: ManagedKnowledgeSearchHit) -> MarketingEvidence:
    return MarketingEvidence(
        document_id=hit.document.id,
        document_name=hit.document.title,
        document_version_id=hit.version.id,
        document_version=hit.version.version_number,
        chunk_id=hit.chunk.id,
        page_number=hit.chunk.page_number,
        section=hit.chunk.section_title,
        similarity_score=round(1.0 - float(hit.distance), 6),
        content=hit.chunk.content,
    )


def _citation(item: MarketingEvidence) -> dict[str, Any]:
    return {
        "document_id": str(item.document_id),
        "document_name": item.document_name,
        "document_version_id": str(item.document_version_id),
        "document_version": item.document_version,
        "chunk_id": str(item.chunk_id),
        "page_number": item.page_number,
        "section": item.section,
        "similarity_score": item.similarity_score,
    }


def _assistant_evidence(item: MarketingEvidence) -> Any:
    from sari_api.domain.knowledge_assistant import KnowledgeAssistantEvidence

    return KnowledgeAssistantEvidence(
        document_id=item.document_id,
        document_name=item.document_name,
        document_version_id=item.document_version_id,
        document_version=item.document_version,
        page_number=item.page_number,
        section=item.section,
        chunk_id=item.chunk_id,
        source_metadata={},
        similarity_score=item.similarity_score,
        content=item.content,
        content_sha256="0" * 64,
    )
