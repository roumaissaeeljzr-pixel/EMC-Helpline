"""
auth/config.py

Configuration centrale de l'authentification.
Les secrets sont lus depuis .env et ne sont jamais codés en dur.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# ENVIRONNEMENT
# ============================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development",
)

IS_PRODUCTION = (
    ENVIRONMENT == "production"
)


# ============================================================
# JWT D'ACCÈS
# ============================================================

JWT_SECRET = os.getenv(
    "JWT_SECRET"
)

if not JWT_SECRET:
    raise RuntimeError(
        "La variable d'environnement "
        "JWT_SECRET est manquante. "
        "Générez-en une et ajoutez-la "
        "à votre fichier .env."
    )


if (
    IS_PRODUCTION
    and len(JWT_SECRET) < 32
):
    raise RuntimeError(
        "JWT_SECRET est trop courte "
        "pour un environnement de production."
    )


JWT_ALGORITHM = "HS256"


ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30",
    )
)


ACCESS_TOKEN_EXPIRE_DELTA = timedelta(
    minutes=ACCESS_TOKEN_EXPIRE_MINUTES
)


# ============================================================
# RÉINITIALISATION DU MOT DE PASSE
# ============================================================

PASSWORD_RESET_EXPIRE_MINUTES = int(
    os.getenv(
        "PASSWORD_RESET_EXPIRE_MINUTES",
        "15",
    )
)


PASSWORD_RESET_EXPIRE_DELTA = timedelta(
    minutes=PASSWORD_RESET_EXPIRE_MINUTES
)


# ============================================================
# VÉRIFICATION DE L'ADRESSE E-MAIL
# ============================================================

EMAIL_VERIFICATION_EXPIRE_MINUTES = int(
    os.getenv(
        "EMAIL_VERIFICATION_EXPIRE_MINUTES",
        "10",
    )
)


EMAIL_VERIFICATION_EXPIRE_DELTA = timedelta(
    minutes=EMAIL_VERIFICATION_EXPIRE_MINUTES
)


# ============================================================
# COOKIES
# ============================================================

ACCESS_TOKEN_COOKIE_NAME = (
    "access_token"
)

CSRF_COOKIE_NAME = (
    "csrf_token"
)

CSRF_HEADER_NAME = (
    "X-CSRF-Token"
)


COOKIE_SECURE = (
    IS_PRODUCTION
)

COOKIE_SAMESITE = "lax"


# ============================================================
# CORS / FRONTEND
# ============================================================

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173",
)


# ============================================================
# E-MAIL / SMTP
# ============================================================

SMTP_HOST = os.getenv(
    "SMTP_HOST"
)


SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587",
    )
)


SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME"
)


SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)


SMTP_FROM_EMAIL = os.getenv(
    "SMTP_FROM_EMAIL",
    SMTP_USERNAME or "",
)


SMTP_USE_TLS = (
    os.getenv(
        "SMTP_USE_TLS",
        "true",
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)