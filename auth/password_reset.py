"""
auth/password_reset.py

Gestion sécurisée de la réinitialisation
du mot de passe avec code OTP à 6 chiffres.
"""

import hashlib
import hmac
import secrets

from datetime import (
    datetime,
    timezone,
)

from typing import Any

import jwt

from auth.config import (
    JWT_ALGORITHM,
    JWT_SECRET,
    PASSWORD_RESET_EXPIRE_DELTA,
)


RESET_PURPOSE = (
    "password_reset_verified"
)


# ============================================================
# CODE OTP
# ============================================================

def generate_reset_code() -> str:
    """
    Génère exactement 6 chiffres.

    Exemples :
        583912
        004821
    """

    return (
        f"{secrets.randbelow(1_000_000):06d}"
    )


def hash_reset_code(
    *,
    user_id: str,
    code: str,
) -> str:
    """
    Le code OTP n'est jamais stocké en clair.

    HMAC-SHA256 :
        secret serveur
        + ID utilisateur
        + code
    """

    message = (
        f"{user_id}:{code}"
        .encode("utf-8")
    )

    return hmac.new(
        JWT_SECRET.encode(
            "utf-8"
        ),
        message,
        hashlib.sha256,
    ).hexdigest()


def reset_code_matches(
    *,
    user_id: str,
    code: str,
    expected_hash: str,
) -> bool:

    candidate_hash = (
        hash_reset_code(
            user_id=user_id,
            code=code,
        )
    )

    return hmac.compare_digest(
        candidate_hash,
        expected_hash,
    )


# ============================================================
# PASSWORD FINGERPRINT
# ============================================================

def password_hash_fingerprint(
    password_hash: str,
) -> str:

    return hashlib.sha256(
        password_hash.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# TOKEN APRÈS VALIDATION DU CODE
# ============================================================

def create_verified_reset_token(
    *,
    user_id: str,
    password_hash: str,
) -> str:
    """
    Ce token n'est jamais envoyé par Gmail.

    Il est créé uniquement après que
    l'utilisateur ait fourni le bon code OTP.
    """

    now = datetime.now(
        timezone.utc
    )

    payload: dict[
        str,
        Any,
    ] = {

        "sub": user_id,

        "purpose":
            RESET_PURPOSE,

        "pwd":
            password_hash_fingerprint(
                password_hash
            ),

        "jti":
            secrets.token_urlsafe(
                24
            ),

        "iat": now,

        "exp":
            now
            + PASSWORD_RESET_EXPIRE_DELTA,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_verified_reset_token(
    token: str,
) -> dict[str, Any]:

    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[
            JWT_ALGORITHM
        ],
    )

    if (
        payload.get("purpose")
        != RESET_PURPOSE
    ):
        raise jwt.InvalidTokenError(
            "Type de token invalide."
        )

    return payload