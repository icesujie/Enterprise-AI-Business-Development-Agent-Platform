from __future__ import annotations

import asyncio
from typing import Any, Protocol
from uuid import UUID

import jwt
from jwt import PyJWKClient

from sari_api.domain.identity import TokenIdentity


class InvalidAccessTokenError(Exception):
    pass


class SigningKeyResolver(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


class SupabaseJwtVerifier:
    """Validate Supabase access tokens locally using asymmetric signing keys."""

    _ALGORITHMS = ("ES256", "RS256")

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        cache_seconds: int,
        key_resolver: SigningKeyResolver | None = None,
    ) -> None:
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._key_resolver = key_resolver or PyJWKClient(
            jwks_url,
            cache_keys=True,
            lifespan=cache_seconds,
        )

    async def verify(self, token: str) -> TokenIdentity:
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") not in self._ALGORITHMS or not header.get("kid"):
                raise InvalidAccessTokenError("unsupported access-token signature")
            signing_key = await asyncio.to_thread(
                self._key_resolver.get_signing_key_from_jwt,
                token,
            )
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self._ALGORITHMS),
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            )
            subject = claims.get("sub")
            if not isinstance(subject, str) or not subject.strip():
                raise InvalidAccessTokenError("access token has no valid subject")
            UUID(subject)
            email_claim = claims.get("email")
            email = email_claim if isinstance(email_claim, str) else None
            return TokenIdentity(subject=subject, email=email)
        except InvalidAccessTokenError:
            raise
        except (jwt.PyJWTError, ValueError, TypeError) as exc:
            raise InvalidAccessTokenError("invalid or expired access token") from exc
