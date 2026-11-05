"""
auth/email_verification.py

Génération et vérification sécurisée
des codes OTP de confirmation d'e-mail.
"""

import hashlib
import hmac
import secrets

from auth.config import (
    JWT_SECRET,
)


# ============================================================
# GÉNÉRATION DU CODE
# ============================================================

def generate_email_verification_code() -> str:
    """
    Génère un code composé exactement
    de six chiffres.
    """

    return (
        f"{secrets.randbelow(1_000_000):06d}"
    )


# ============================================================
# HACHAGE DU CODE
# ============================================================

def hash_email_verification_code(
    *,
    user_id: str,
    code: str,
) -> str:
    """
    Le code n'est jamais conservé
    en clair dans PostgreSQL.

    Le préfixe email_verification sépare
    ce code des codes de réinitialisation.
    """

    message = (
        f"email_verification:{user_id}:{code}"
        .encode("utf-8")
    )

    return hmac.new(
        JWT_SECRET.encode(
            "utf-8"
        ),
        message,
        hashlib.sha256,
    ).hexdigest()


# ============================================================
# COMPARAISON
# ============================================================

def email_verification_code_matches(
    *,
    user_id: str,
    code: str,
    expected_hash: str,
) -> bool:
    """
    Compare de manière sécurisée le code fourni
    avec l'empreinte enregistrée.
    """

    candidate_hash = (
        hash_email_verification_code(
            user_id=user_id,
            code=code,
        )
    )

    return hmac.compare_digest(
        candidate_hash,
        expected_hash,
    )