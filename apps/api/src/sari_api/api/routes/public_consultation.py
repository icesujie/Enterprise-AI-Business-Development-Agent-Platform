from __future__ import annotations

import hashlib
import logging
import time
from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from redis.exceptions import RedisError

from sari_api.adapters.public_consultation_provider import (
    MockPublicConsultationProvider,
    build_public_consultation_provider,
)
from sari_api.adapters.rate_limit import consume_fixed_window
from sari_api.core.config import get_settings
from sari_api.core.observability import get_correlation_id
from sari_api.domain.public_consultation import (
    PROMPTS,
    InvalidPublicConsultationInputError,
    PublicConsultationField,
    PublicConsultationLanguage,
    next_field,
    validate_public_answer,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/public/consultation", tags=["public consultation"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PublicConsultationTurnInput(StrictModel):
    language: PublicConsultationLanguage
    field: PublicConsultationField
    answer: str = Field(min_length=1, max_length=500)


class PublicConsultationTurnResponse(StrictModel):
    accepted_value: str
    assistant_message: str
    next_field: PublicConsultationField | None
    next_prompt: str | None
    ready_for_consent: bool
    provider_type: str
    correlation_id: str


async def enforce_public_consultation_rate_limit(request: Request) -> None:
    settings = get_settings()
    host = request.client.host if request.client else "unknown"
    digest = hashlib.sha256(host.encode()).hexdigest()[:24]
    try:
        allowed, retry_after = await consume_fixed_window(
            redis_url=settings.redis_url,
            key=f"rate:public-consultation:{digest}",
            limit=settings.public_consultation_rate_limit,
            window_seconds=settings.public_rate_window_seconds,
        )
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="Consultation service is unavailable.") from exc
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many consultation messages.",
            headers={"Retry-After": str(max(retry_after, 1))},
        )


@router.post(
    "/turns",
    response_model=PublicConsultationTurnResponse,
    dependencies=[Depends(enforce_public_consultation_rate_limit)],
)
async def process_public_consultation_turn(
    payload: PublicConsultationTurnInput,
    site_token: Annotated[str, Header(alias="X-Site-Token")],
) -> PublicConsultationTurnResponse:
    settings = get_settings()
    if not compare_digest(site_token, settings.public_site_token):
        raise HTTPException(status_code=401, detail="Invalid site token.")
    try:
        accepted = validate_public_answer(payload.field, payload.answer)
    except InvalidPublicConsultationInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    following = next_field(payload.field)
    prompt = PROMPTS[payload.language][following] if following else None
    # Names, companies, and email addresses never need an external model call.
    provider = (
        MockPublicConsultationProvider()
        if payload.field in {"contact_name", "company", "email"}
        else build_public_consultation_provider(settings)
    )
    started = time.perf_counter()
    try:
        reply = await provider.respond(
            language=payload.language,
            field=payload.field,
            answer=accepted,
            next_field=following,
            next_prompt=prompt,
        )
    except Exception:
        logger.exception(
            "Public consultation provider failed",
            extra={
                "event": "public_consultation.provider_failed",
                "language": payload.language,
                "provider_type": provider.provider_type,
                "outcome": "deterministic_fallback",
            },
        )
        provider = MockPublicConsultationProvider()
        reply = await provider.respond(
            language=payload.language,
            field=payload.field,
            answer=accepted,
            next_field=following,
            next_prompt=prompt,
        )
    logger.info(
        "Public consultation turn completed",
        extra={
            "event": "public_consultation.turn.completed",
            "language": payload.language,
            "provider_type": provider.provider_type,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "outcome": "accepted",
        },
    )
    return PublicConsultationTurnResponse(
        accepted_value=accepted,
        assistant_message=reply.assistant_message,
        next_field=following,
        next_prompt=prompt,
        ready_for_consent=following is None,
        provider_type=provider.provider_type,
        correlation_id=get_correlation_id(),
    )
