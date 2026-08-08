from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from sari_api.adapters.auth import InvalidAccessTokenError, SupabaseJwtVerifier

ISSUER = "https://test.supabase.example/auth/v1"
AUDIENCE = "authenticated"
KEY_ID = "m2-test-key"


class SigningKey:
    def __init__(self, key: Any) -> None:
        self.key = key


class StaticKeyResolver:
    def __init__(self, key: Any) -> None:
        self._key = SigningKey(key)

    def get_signing_key_from_jwt(self, token: str) -> SigningKey:
        assert token
        return self._key


def build_verifier(public_key: Any) -> SupabaseJwtVerifier:
    return SupabaseJwtVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks_url=f"{ISSUER}/.well-known/jwks.json",
        cache_seconds=600,
        key_resolver=StaticKeyResolver(public_key),
    )


def build_token(private_key: Any, **overrides: Any) -> str:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "30000000-0000-4000-8000-000000000001",
        "email": "admin@sari-arta.example",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": KEY_ID})


@pytest.mark.asyncio
async def test_verifier_accepts_valid_asymmetric_supabase_token() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    identity = await build_verifier(private_key.public_key()).verify(build_token(private_key))

    assert identity.subject == "30000000-0000-4000-8000-000000000001"
    assert identity.email == "admin@sari-arta.example"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claim_overrides",
    [
        {"aud": "wrong-audience"},
        {"iss": "https://attacker.example/auth/v1"},
        {"exp": datetime.now(UTC) - timedelta(seconds=1)},
        {"sub": ""},
        {"sub": "not-a-supabase-user-id"},
    ],
)
async def test_verifier_rejects_invalid_required_claims(
    claim_overrides: dict[str, Any],
) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    with pytest.raises(InvalidAccessTokenError):
        await build_verifier(private_key.public_key()).verify(
            build_token(private_key, **claim_overrides)
        )


@pytest.mark.asyncio
async def test_verifier_rejects_symmetric_algorithm() -> None:
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "30000000-0000-4000-8000-000000000001",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        "not-a-production-secret-32-bytes-long",
        algorithm="HS256",
        headers={"kid": KEY_ID},
    )

    with pytest.raises(InvalidAccessTokenError):
        await build_verifier(object()).verify(token)
