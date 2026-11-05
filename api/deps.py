"""
api/deps.py

Dépendances FastAPI pour l'authentification :
    get_current_user -- extrait et valide le JWT depuis le cookie,
                         vérifie is_active
    require_role      -- factory de dépendance pour restreindre un
                         endpoint à un ou plusieurs rôles
    verify_csrf        -- pattern double-submit cookie, à utiliser sur
                         tout endpoint authentifié qui MODIFIE des
                         données (POST/PUT/PATCH/DELETE)

Indépendant du pipeline IA/RAG existant.
"""

import uuid

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.config import (
    ACCESS_TOKEN_COOKIE_NAME,
    CSRF_HEADER_NAME,
    JWT_ALGORITHM,
    JWT_SECRET,
)
from db.database import get_db
from db.models import User, UserRole


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    Extrait le JWT depuis le cookie HttpOnly, le valide, récupère
    l'utilisateur correspondant et vérifie is_active.

    Le payload décodé est stocké sur request.state.token_payload
    pour que verify_csrf() puisse le réutiliser sans redécoder le
    token une seconde fois.
    """

    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié.",
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée. Veuillez vous reconnecter.",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide.",
        )

    user_id_raw = payload.get("sub")

    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide.",
        )

    try:
        user_id = uuid.UUID(user_id_raw)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide.",
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    request.state.token_payload = payload

    return user


def require_role(*allowed_roles: UserRole):
    """
    Factory de dépendance : restreint un endpoint à un ou plusieurs
    rôles.

    Exemple d'usage futur :
        @router.get("/admin/statistics")
        def stats(user: User = Depends(require_role(UserRole.admin))):
            ...
    """

    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce rôle.",
            )

        return current_user

    return dependency


def verify_csrf(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Pattern double-submit cookie : la valeur du claim "csrf" du JWT
    (déjà décodé par get_current_user, réutilisé via request.state)
    doit correspondre exactement à l'en-tête X-CSRF-Token envoyé par
    le frontend.

    À utiliser UNIQUEMENT sur les endpoints authentifiés qui modifient
    des données (POST/PUT/PATCH/DELETE) -- jamais sur les endpoints en
    lecture seule (GET), qui n'ont pas à être protégés contre le CSRF.
    """

    payload = getattr(request.state, "token_payload", None)
    expected_csrf = payload.get("csrf") if payload else None

    provided_csrf = request.headers.get(CSRF_HEADER_NAME)

    if not expected_csrf or not provided_csrf or provided_csrf != expected_csrf:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Jeton CSRF invalide ou manquant.",
        )