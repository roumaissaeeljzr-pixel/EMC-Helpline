"""
auth/security.py

Hachage des mots de passe (pwdlib[argon2]) et création/décodage des
JWT (PyJWT). Aucune dépendance au pipeline IA/RAG.
"""

import secrets
from datetime import datetime, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from auth.config import (
    ACCESS_TOKEN_EXPIRE_DELTA,
    JWT_ALGORITHM,
    JWT_SECRET,
)

# PasswordHash.recommended() utilise Argon2 (argon2id) comme schéma
# principal -- confirmé par inspection du hash produit ("$argon2id$...").
_password_hasher = PasswordHash.recommended()


# ============================================================
# MOTS DE PASSE
# ============================================================

def hash_password(password: str) -> str:
    """
    Retourne le hash Argon2 du mot de passe. Le mot de passe en clair
    n'est jamais conservé au-delà de cet appel.
    """

    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Vérifie un mot de passe contre son hash. Retourne False plutôt
    que de lever une exception en cas de hash malformé -- ne doit
    jamais faire planter /auth/login.
    """

    try:
        return _password_hasher.verify(password, password_hash)
    except Exception:
        return False


# ============================================================
# JWT
# ============================================================

def create_access_token(user_id: str, role: str) -> tuple[str, str]:
    """
    Crée un JWT d'accès contenant un claim CSRF aléatoire (voir
    api/deps.py : verify_csrf pour son utilisation).

    Retourne (token, csrf_value) -- csrf_value est posé séparément
    comme cookie non-HttpOnly par l'appelant (api/routers/auth.py).
    """

    now = datetime.now(timezone.utc)
    csrf_value = secrets.token_urlsafe(32)

    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "csrf": csrf_value,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_DELTA,
    }

    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return token, csrf_value


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Décode et valide un JWT d'accès. Lève jwt.ExpiredSignatureError
    ou jwt.InvalidTokenError -- géré par l'appelant (api/deps.py),
    jamais ici, pour rester une fonction pure de bas niveau.
    """

    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )