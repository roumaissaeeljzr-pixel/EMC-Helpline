"""
auth/pii_crypto.py

Chiffrement applicatif des données personnelles sensibles.

La clé doit rester uniquement dans .env :
PII_ENCRYPTION_KEY=...

Ne jamais :
- committer cette clé ;
- l'afficher dans le frontend ;
- la partager dans les logs.
"""

import os

from cryptography.fernet import (
    Fernet,
    InvalidToken,
)
from dotenv import load_dotenv


load_dotenv()


PII_ENCRYPTION_KEY = os.getenv(
    "PII_ENCRYPTION_KEY"
)


if not PII_ENCRYPTION_KEY:
    raise RuntimeError(
        "PII_ENCRYPTION_KEY est manquante. "
        "Générez une clé Fernet et ajoutez-la à .env."
    )


try:
    _fernet = Fernet(
        PII_ENCRYPTION_KEY.encode(
            "utf-8"
        )
    )
except Exception as exc:
    raise RuntimeError(
        "PII_ENCRYPTION_KEY n'est pas une clé Fernet valide."
    ) from exc


def encrypt_sensitive(
    value: str,
) -> str:
    clean = value.strip()

    if not clean:
        raise ValueError(
            "La valeur à chiffrer ne peut pas être vide."
        )

    return _fernet.encrypt(
        clean.encode(
            "utf-8"
        )
    ).decode(
        "utf-8"
    )


def decrypt_sensitive(
    token: str | None,
) -> str | None:
    if not token:
        return None

    try:
        return _fernet.decrypt(
            token.encode(
                "utf-8"
            )
        ).decode(
            "utf-8"
        )
    except InvalidToken as exc:
        raise RuntimeError(
            "Impossible de déchiffrer la donnée sensible."
        ) from exc
