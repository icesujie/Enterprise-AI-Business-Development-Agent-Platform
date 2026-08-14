from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sari_api.adapters.models import (
    Agent,
    DomainPackage,
    KnowledgeAuditLog,
    KnowledgeCollection,
    KnowledgeDocumentAgentBinding,
    KnowledgeDocumentVersion,
    KnowledgeProcessingRun,
    ManagedKnowledgeDocument,
    User,
)


class EnterpriseKnowledgeNotFoundError(Exception):
    pass


class EnterpriseKnowledgeStateError(Exception):
    pass


class EnterpriseKnowledgeAccessError(Exception):
    pass


class EnterpriseKnowledgeConcurrencyError(Exception):
    pass


class EnterpriseKnowledgeRepository:
    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def set_tenant_context(self) -> None:
        await self._session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self._tenant_id)},
        )

    async def get_domain(self, domain_key: str) -> DomainPackage:
        domain = await self._session.scalar(
            select(DomainPackage).where(DomainPackage.domain_key == domain_key)
        )
        if domain is None:
            raise EnterpriseKnowledgeNotFoundError
        return domain

    async def create_collection(
        self,
        *,
        domain_key: str,
        collection_key: str,
        name: str,
        description: str | None,
        collection_metadata: dict[str, Any],
        created_by: UUID,
    ) -> tuple[KnowledgeCollection, DomainPackage]:
        domain = await self.get_domain(domain_key)
        collection = KnowledgeCollection(
            tenant_id=self._tenant_id,
            domain_package_id=domain.id,
            collection_key=collection_key,
            name=name,
            description=description,
            collection_metadata=collection_metadata,
            created_by=created_by,
        )
        self._session.add(collection)
        await self._session.flush()
        return collection, domain

    async def get_collection(
        self, collection_id: UUID, *, lock: bool = False
    ) -> tuple[KnowledgeCollection, DomainPackage]:
        statement = (
            select(KnowledgeCollection, DomainPackage)
            .join(DomainPackage, DomainPackage.id == KnowledgeCollection.domain_package_id)
            .where(
                KnowledgeCollection.id == collection_id,
                KnowledgeCollection.tenant_id == self._tenant_id,
            )
        )
        if lock:
            statement = statement.with_for_update(of=KnowledgeCollection)
        row = (await self._session.execute(statement)).tuples().one_or_none()
        if row is None:
            raise EnterpriseKnowledgeNotFoundError
        return row

    async def list_collections(
        self, *, domain_key: str | None = None, search: str | None = None
    ) -> list[tuple[KnowledgeCollection, DomainPackage, int]]:
        document_count = (
            select(
                ManagedKnowledgeDocument.collection_id,
                func.count().label("document_count"),
            )
            .where(ManagedKnowledgeDocument.tenant_id == self._tenant_id)
            .group_by(ManagedKnowledgeDocument.collection_id)
            .subquery()
        )
        statement = (
            select(
                KnowledgeCollection,
                DomainPackage,
                func.coalesce(document_count.c.document_count, 0),
            )
            .join(DomainPackage, DomainPackage.id == KnowledgeCollection.domain_package_id)
            .outerjoin(document_count, document_count.c.collection_id == KnowledgeCollection.id)
            .where(KnowledgeCollection.tenant_id == self._tenant_id)
        )
        if domain_key:
            statement = statement.where(DomainPackage.domain_key == domain_key)
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    KnowledgeCollection.name.ilike(pattern),
                    KnowledgeCollection.description.ilike(pattern),
                )
            )
        rows = (await self._session.execute(statement.order_by(KnowledgeCollection.name))).all()
        return [(collection, domain, int(count)) for collection, domain, count in rows]

    async def create_document(
        self,
        *,
        collection_id: UUID,
        title: str,
        document_type: str,
        language: str,
        original_filename: str,
        media_type: str,
        object_key: str,
        content_sha256: str,
        byte_size: int,
        document_metadata: dict[str, Any],
        created_by: UUID,
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        collection, _ = await self.get_collection(collection_id)
        if collection.status != "active":
            raise EnterpriseKnowledgeStateError
        document = ManagedKnowledgeDocument(
            tenant_id=self._tenant_id,
            domain_package_id=collection.domain_package_id,
            collection_id=collection.id,
            title=title,
            document_type=document_type,
            language=language,
            lifecycle_status="uploaded",
            document_metadata=document_metadata,
            created_by=created_by,
        )
        self._session.add(document)
        await self._session.flush()
        version = KnowledgeDocumentVersion(
            tenant_id=self._tenant_id,
            document_id=document.id,
            version_number=1,
            original_filename=original_filename,
            media_type=media_type,
            object_key=object_key,
            content_sha256=content_sha256,
            byte_size=byte_size,
            version_metadata=document_metadata,
            created_by=created_by,
        )
        self._session.add(version)
        await self._session.flush()
        document.current_version_id = version.id
        document.updated_by = created_by
        return document, version

    async def list_documents(
        self,
        *,
        collection_id: UUID | None = None,
        domain_key: str | None = None,
        agent_key: str | None = None,
        lifecycle_status: str | None = None,
        search: str | None = None,
    ) -> list[tuple[ManagedKnowledgeDocument, KnowledgeCollection, DomainPackage]]:
        statement = (
            select(ManagedKnowledgeDocument, KnowledgeCollection, DomainPackage)
            .join(
                KnowledgeCollection,
                KnowledgeCollection.id == ManagedKnowledgeDocument.collection_id,
            )
            .join(DomainPackage, DomainPackage.id == ManagedKnowledgeDocument.domain_package_id)
            .where(ManagedKnowledgeDocument.tenant_id == self._tenant_id)
        )
        if collection_id:
            statement = statement.where(ManagedKnowledgeDocument.collection_id == collection_id)
        if domain_key:
            statement = statement.where(DomainPackage.domain_key == domain_key)
        if lifecycle_status:
            statement = statement.where(
                ManagedKnowledgeDocument.lifecycle_status == lifecycle_status
            )
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    ManagedKnowledgeDocument.title.ilike(pattern),
                    ManagedKnowledgeDocument.document_type.ilike(pattern),
                )
            )
        if agent_key:
            statement = (
                statement.join(
                    KnowledgeDocumentAgentBinding,
                    KnowledgeDocumentAgentBinding.document_id == ManagedKnowledgeDocument.id,
                )
                .join(Agent, Agent.id == KnowledgeDocumentAgentBinding.agent_id)
                .where(
                    Agent.agent_key == agent_key,
                    KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id,
                    KnowledgeDocumentAgentBinding.status == "enabled",
                )
            )
        return list(
            (
                await self._session.execute(
                    statement.order_by(ManagedKnowledgeDocument.updated_at.desc())
                )
            )
            .tuples()
            .all()
        )

    async def get_document(
        self, document_id: UUID, *, lock: bool = False
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeCollection, DomainPackage]:
        statement = (
            select(ManagedKnowledgeDocument, KnowledgeCollection, DomainPackage)
            .join(
                KnowledgeCollection,
                KnowledgeCollection.id == ManagedKnowledgeDocument.collection_id,
            )
            .join(DomainPackage, DomainPackage.id == ManagedKnowledgeDocument.domain_package_id)
            .where(
                ManagedKnowledgeDocument.id == document_id,
                ManagedKnowledgeDocument.tenant_id == self._tenant_id,
            )
        )
        if lock:
            statement = statement.with_for_update(of=ManagedKnowledgeDocument).execution_options(
                populate_existing=True
            )
        row = (await self._session.execute(statement)).tuples().one_or_none()
        if row is None:
            raise EnterpriseKnowledgeNotFoundError
        return row

    async def current_version(self, document: ManagedKnowledgeDocument) -> KnowledgeDocumentVersion:
        criteria = [
            KnowledgeDocumentVersion.tenant_id == self._tenant_id,
            KnowledgeDocumentVersion.document_id == document.id,
        ]
        if document.current_version_id is not None:
            criteria.append(KnowledgeDocumentVersion.id == document.current_version_id)
        else:
            criteria.append(
                KnowledgeDocumentVersion.version_number == document.current_version_number
            )
        version = await self._session.scalar(select(KnowledgeDocumentVersion).where(*criteria))
        if version is None:
            raise EnterpriseKnowledgeNotFoundError
        return version

    async def get_version(self, document_id: UUID, version_id: UUID) -> KnowledgeDocumentVersion:
        await self.get_document(document_id)
        version = await self._session.scalar(
            select(KnowledgeDocumentVersion).where(
                KnowledgeDocumentVersion.id == version_id,
                KnowledgeDocumentVersion.document_id == document_id,
                KnowledgeDocumentVersion.tenant_id == self._tenant_id,
            )
        )
        if version is None:
            raise EnterpriseKnowledgeNotFoundError
        return version

    async def list_versions(self, document_id: UUID) -> list[KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id)
        return list(
            (
                await self._session.scalars(
                    select(KnowledgeDocumentVersion)
                    .where(
                        KnowledgeDocumentVersion.tenant_id == self._tenant_id,
                        KnowledgeDocumentVersion.document_id == document.id,
                    )
                    .order_by(KnowledgeDocumentVersion.version_number.desc())
                )
            ).all()
        )

    @staticmethod
    def _check_record_version(document: ManagedKnowledgeDocument, expected_version: int) -> None:
        if document.version != expected_version:
            raise EnterpriseKnowledgeConcurrencyError

    @staticmethod
    def _advance_record_version(document: ManagedKnowledgeDocument, actor_id: UUID) -> None:
        document.version += 1
        document.updated_by = actor_id

    async def update_document_metadata(
        self,
        document_id: UUID,
        *,
        expected_version: int,
        actor_id: UUID,
        title: str | None,
        document_type: str | None,
        language: str | None,
        document_metadata: dict[str, Any] | None,
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id, lock=True)
        self._check_record_version(document, expected_version)
        if document.lifecycle_status in {"active", "archived"}:
            raise EnterpriseKnowledgeStateError
        if title is not None:
            document.title = title
        if document_type is not None:
            document.document_type = document_type
        if language is not None:
            document.language = language
        if document_metadata is not None:
            document.document_metadata = document_metadata
        version = await self.current_version(document)
        if document.lifecycle_status in {"review", "approved", "published"}:
            document.lifecycle_status = "uploaded"
            document.approval_status = "pending"
            document.approved_by = None
            document.approved_at = None
            document.published_version_id = None
            document.published_by = None
            document.published_at = None
            version.status = "uploaded"
            version.review_status = "pending"
            version.reviewed_by = None
            version.reviewed_at = None
            version.review_note = None
        document.processing_status = "uploaded"
        self._advance_record_version(document, actor_id)
        return document, version

    async def create_new_version(
        self,
        document_id: UUID,
        *,
        expected_version: int,
        actor_id: UUID,
        original_filename: str,
        media_type: str,
        object_key: str,
        content_sha256: str,
        byte_size: int,
        version_metadata: dict[str, Any],
        restored_from_version_id: UUID | None = None,
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, collection, _ = await self.get_document(document_id, lock=True)
        self._check_record_version(document, expected_version)
        if collection.status != "active":
            raise EnterpriseKnowledgeStateError
        if restored_from_version_id is not None:
            await self.get_version(document_id, restored_from_version_id)
        next_number = document.current_version_number + 1
        version = KnowledgeDocumentVersion(
            tenant_id=self._tenant_id,
            document_id=document.id,
            version_number=next_number,
            original_filename=original_filename,
            media_type=media_type,
            object_key=object_key,
            content_sha256=content_sha256,
            byte_size=byte_size,
            version_metadata=version_metadata,
            status="uploaded",
            review_status="pending",
            restored_from_version_id=restored_from_version_id,
            created_from_action="rollback" if restored_from_version_id else "upload",
            created_by=actor_id,
        )
        self._session.add(version)
        await self._session.flush()
        document.current_version_number = next_number
        document.current_version_id = version.id
        document.lifecycle_status = "uploaded"
        document.approval_status = "pending"
        document.processing_status = "uploaded"
        document.approved_by = None
        document.approved_at = None
        document.review_note = None
        self._advance_record_version(document, actor_id)
        return document, version

    async def submit_for_review(
        self, document_id: UUID, *, actor_id: UUID | None = None
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id, lock=True)
        if document.lifecycle_status != "uploaded":
            raise EnterpriseKnowledgeStateError
        version = await self.current_version(document)
        document.lifecycle_status = "processing"
        version.status = "processing"
        await self._session.flush()
        document.lifecycle_status = "review"
        document.approval_status = "pending"
        version.status = "review"
        version.review_status = "pending"
        if actor_id is not None:
            self._advance_record_version(document, actor_id)
        return document, version

    async def review_document(
        self,
        document_id: UUID,
        *,
        reviewer_id: UUID,
        decision: str,
        note: str | None,
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id, lock=True)
        if document.lifecycle_status != "review" or document.approval_status != "pending":
            raise EnterpriseKnowledgeStateError
        version = await self.current_version(document)
        document.review_note = note
        now = datetime.now(UTC)
        version.reviewed_by = reviewer_id
        version.reviewed_at = now
        version.review_note = note
        if decision == "approved":
            document.lifecycle_status = "approved"
            document.approval_status = "approved"
            document.approved_by = reviewer_id
            document.approved_at = now
            version.status = "approved"
            version.review_status = "approved"
        else:
            document.approval_status = "rejected"
            version.status = "rejected"
            version.review_status = "rejected"
        self._advance_record_version(document, reviewer_id)
        return document, version

    async def publish_document(
        self, document_id: UUID, *, publisher_id: UUID
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id, lock=True)
        if document.lifecycle_status != "approved" or document.approval_status != "approved":
            raise EnterpriseKnowledgeStateError
        version = await self.current_version(document)
        if version.review_status != "approved":
            raise EnterpriseKnowledgeStateError
        document.lifecycle_status = "published"
        document.published_version_id = version.id
        document.published_by = publisher_id
        document.published_at = datetime.now(UTC)
        version.status = "published"
        self._advance_record_version(document, publisher_id)
        return document, version

    async def activate_document(
        self, document_id: UUID, *, publisher_id: UUID | None = None
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id, lock=True)
        if document.lifecycle_status != "published" or document.published_version_id is None:
            raise EnterpriseKnowledgeStateError
        binding = await self._session.scalar(
            select(KnowledgeDocumentAgentBinding.id).where(
                KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id,
                KnowledgeDocumentAgentBinding.document_id == document.id,
                KnowledgeDocumentAgentBinding.status == "enabled",
            )
        )
        if binding is None:
            raise EnterpriseKnowledgeAccessError
        version = await self.get_version(document.id, document.published_version_id)
        if document.active_version_id is not None and document.active_version_id != version.id:
            previous = await self.get_version(document.id, document.active_version_id)
            previous.status = "superseded"
        document.lifecycle_status = "active"
        document.active_version_id = version.id
        version.status = "active"
        if publisher_id is not None:
            self._advance_record_version(document, publisher_id)
        return document, version

    async def archive_document(
        self, document_id: UUID, *, actor_id: UUID | None = None, reason: str | None = None
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id, lock=True)
        if document.lifecycle_status not in {"approved", "published", "active"}:
            raise EnterpriseKnowledgeStateError
        version_id = document.active_version_id or document.published_version_id
        version = (
            await self.get_version(document.id, version_id)
            if version_id is not None
            else await self.current_version(document)
        )
        document.lifecycle_status = "archived"
        document.active_version_id = None
        document.archived_by = actor_id
        document.archived_at = datetime.now(UTC)
        document.archive_reason = reason
        version.status = "archived"
        if actor_id is not None:
            self._advance_record_version(document, actor_id)
        return document, version

    async def restore_document(
        self, document_id: UUID, *, actor_id: UUID, reason: str
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeDocumentVersion]:
        document, _, _ = await self.get_document(document_id, lock=True)
        if document.lifecycle_status != "archived":
            raise EnterpriseKnowledgeStateError
        version_id = document.published_version_id or document.current_version_id
        if version_id is None:
            raise EnterpriseKnowledgeStateError
        version = await self.get_version(document.id, version_id)
        document.current_version_id = version.id
        document.current_version_number = version.version_number
        document.lifecycle_status = "approved" if version.review_status == "approved" else "review"
        document.approval_status = version.review_status
        document.active_version_id = None
        document.restore_reason = reason
        version.status = "approved" if version.review_status == "approved" else "review"
        self._advance_record_version(document, actor_id)
        return document, version

    async def bind_document(
        self, document_id: UUID, *, agent_key: str, created_by: UUID
    ) -> tuple[KnowledgeDocumentAgentBinding, Agent]:
        document, _, _ = await self.get_document(document_id)
        agent = await self._session.scalar(select(Agent).where(Agent.agent_key == agent_key))
        if agent is None:
            raise EnterpriseKnowledgeNotFoundError
        if agent.domain_package_id != document.domain_package_id:
            raise EnterpriseKnowledgeAccessError
        existing = await self._session.scalar(
            select(KnowledgeDocumentAgentBinding).where(
                KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id,
                KnowledgeDocumentAgentBinding.document_id == document.id,
                KnowledgeDocumentAgentBinding.agent_id == agent.id,
            )
        )
        if existing is not None:
            if existing.status == "enabled":
                raise EnterpriseKnowledgeStateError
            existing.status = "enabled"
            existing.updated_by = created_by
            existing.updated_at = datetime.now(UTC)
            document.agent_id = agent.id
            return existing, agent
        binding = KnowledgeDocumentAgentBinding(
            tenant_id=self._tenant_id,
            document_id=document.id,
            agent_id=agent.id,
            status="enabled",
            created_by=created_by,
        )
        document.agent_id = agent.id
        self._session.add(binding)
        await self._session.flush()
        return binding, agent

    async def update_binding(
        self,
        document_id: UUID,
        binding_id: UUID,
        *,
        status: str,
        actor_id: UUID,
    ) -> tuple[KnowledgeDocumentAgentBinding, Agent, ManagedKnowledgeDocument]:
        document, _, _ = await self.get_document(document_id, lock=True)
        row = (
            (
                await self._session.execute(
                    select(KnowledgeDocumentAgentBinding, Agent)
                    .join(Agent, Agent.id == KnowledgeDocumentAgentBinding.agent_id)
                    .where(
                        KnowledgeDocumentAgentBinding.id == binding_id,
                        KnowledgeDocumentAgentBinding.document_id == document_id,
                        KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id,
                    )
                    .with_for_update(of=KnowledgeDocumentAgentBinding)
                )
            )
            .tuples()
            .one_or_none()
        )
        if row is None:
            raise EnterpriseKnowledgeNotFoundError
        binding, agent = row
        binding.status = status
        binding.updated_by = actor_id
        binding.updated_at = datetime.now(UTC)
        if status == "disabled":
            remaining = await self._session.scalar(
                select(KnowledgeDocumentAgentBinding.id).where(
                    KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id,
                    KnowledgeDocumentAgentBinding.document_id == document.id,
                    KnowledgeDocumentAgentBinding.id != binding.id,
                    KnowledgeDocumentAgentBinding.status == "enabled",
                )
            )
            if remaining is None:
                document.agent_id = None
                document.active_version_id = None
                if document.lifecycle_status == "active":
                    document.lifecycle_status = "published"
        else:
            document.agent_id = agent.id
        self._advance_record_version(document, actor_id)
        return binding, agent, document

    async def list_bindings(
        self, document_id: UUID
    ) -> list[tuple[KnowledgeDocumentAgentBinding, Agent]]:
        await self.get_document(document_id)
        return list(
            (
                await self._session.execute(
                    select(KnowledgeDocumentAgentBinding, Agent)
                    .join(Agent, Agent.id == KnowledgeDocumentAgentBinding.agent_id)
                    .where(
                        KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id,
                        KnowledgeDocumentAgentBinding.document_id == document_id,
                    )
                    .order_by(Agent.agent_key)
                )
            )
            .tuples()
            .all()
        )

    async def create_processing_run(
        self,
        document_id: UUID,
        *,
        created_by: UUID,
        chunk_size: int,
        chunk_overlap: int,
        embedding_provider: str,
        embedding_model: str,
        embedding_dimensions: int,
        correlation_id: str | None,
    ) -> tuple[ManagedKnowledgeDocument, KnowledgeProcessingRun]:
        document, collection, domain = await self.get_document(document_id, lock=True)
        version = await self.current_version(document)
        if (
            document.approval_status != "approved"
            or document.lifecycle_status not in {"approved", "published", "active"}
            or collection.status != "active"
        ):
            raise EnterpriseKnowledgeStateError
        enabled_binding = await self._session.scalar(
            select(KnowledgeDocumentAgentBinding.id).where(
                KnowledgeDocumentAgentBinding.tenant_id == self._tenant_id,
                KnowledgeDocumentAgentBinding.document_id == document.id,
                KnowledgeDocumentAgentBinding.status == "enabled",
            )
        )
        if enabled_binding is None:
            raise EnterpriseKnowledgeAccessError
        running = await self._session.scalar(
            select(KnowledgeProcessingRun.id).where(
                KnowledgeProcessingRun.tenant_id == self._tenant_id,
                KnowledgeProcessingRun.document_id == document.id,
                KnowledgeProcessingRun.status.in_({"uploaded", "processing"}),
            )
        )
        if running is not None:
            raise EnterpriseKnowledgeStateError
        snapshot = {
            "tenant_id": str(self._tenant_id),
            "domain_key": domain.domain_key,
            "domain_package_id": str(domain.id),
            "collection_id": str(collection.id),
            "collection_key": collection.collection_key,
            "collection_name": collection.name,
            "document_id": str(document.id),
            "document_title": document.title,
            "document_type": document.document_type,
            "language": document.language,
            "document_metadata": document.document_metadata,
            "document_version_id": str(version.id),
            "version_number": version.version_number,
            "version_metadata": version.version_metadata,
            "filename": version.original_filename,
            "content_sha256": version.content_sha256,
        }
        run = KnowledgeProcessingRun(
            tenant_id=self._tenant_id,
            document_id=document.id,
            document_version_id=version.id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            source_metadata_snapshot=snapshot,
            correlation_id=correlation_id,
            created_by=created_by,
        )
        document.processing_status = "uploaded"
        self._session.add(run)
        await self._session.flush()
        return document, run

    async def get_processing_run(self, run_id: UUID) -> KnowledgeProcessingRun:
        run = await self._session.scalar(
            select(KnowledgeProcessingRun).where(
                KnowledgeProcessingRun.id == run_id,
                KnowledgeProcessingRun.tenant_id == self._tenant_id,
            )
        )
        if run is None:
            raise EnterpriseKnowledgeNotFoundError
        return run

    async def list_audit_logs(self, document_id: UUID) -> list[tuple[KnowledgeAuditLog, User]]:
        await self.get_document(document_id)
        return list(
            (
                await self._session.execute(
                    select(KnowledgeAuditLog, User)
                    .join(User, User.id == KnowledgeAuditLog.actor_user_id)
                    .where(
                        KnowledgeAuditLog.tenant_id == self._tenant_id,
                        KnowledgeAuditLog.document_id == document_id,
                    )
                    .order_by(KnowledgeAuditLog.created_at.desc())
                )
            )
            .tuples()
            .all()
        )
