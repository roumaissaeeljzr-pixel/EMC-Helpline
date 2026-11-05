"""
db/schemas.py

Schémas Pydantic pour l'authentification.

Les schémas Pydantic sont séparés des modèles
SQLAlchemy afin de ne jamais exposer les champs
sensibles comme password_hash.
"""

import re
import uuid

from datetime import (
    datetime,
)

from typing import (
    Literal,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from db.models import (
    CaseStatus,
    UserRole,
)


# ============================================================
# INSCRIPTION
# ============================================================

class UserRegister(
    BaseModel
):
    """
    Requête d'inscription publique.

    Aucun champ role n'est accepté.
    Une inscription publique crée toujours
    un compte victime.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    language: Literal[
        "fr",
        "ar",
    ] = "fr"

    @field_validator(
        "username"
    )
    @classmethod
    def username_format(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not re.match(
            r"^[a-zA-Z0-9_.-]+$",
            value,
        ):
            raise ValueError(
                "Le nom d'utilisateur ne peut "
                "contenir que des lettres, "
                "chiffres, points, tirets "
                "et underscores."
            )

        return value


# ============================================================
# CONNEXION
# ============================================================

class UserLogin(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid"
    )

    username: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )


# ============================================================
# RÉPONSE PUBLIQUE
# ============================================================

class UserPublic(
    BaseModel
):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID

    username: str

    email: str

    role: UserRole

    is_active: bool

    email_verified: bool

    email_verified_at: (
        datetime | None
    )

    created_at: datetime


# ============================================================
# VÉRIFICATION DE L'ADRESSE E-MAIL
# ============================================================

class VerifyEmailRequest(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid"
    )

    email: EmailStr

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
    )

    @field_validator(
        "code"
    )
    @classmethod
    def code_format(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if (
            len(value) != 6
            or not value.isdigit()
        ):
            raise ValueError(
                "Le code doit contenir "
                "exactement 6 chiffres."
            )

        return value


class ResendVerificationCodeRequest(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid"
    )

    email: EmailStr

    language: Literal[
        "fr",
        "ar",
    ] = "fr"


# ============================================================
# DOSSIERS VICTIME
# ============================================================

class CaseCreate(
    BaseModel
):
    """
    Création d'un dossier par la victime.

    L'intention, la langue et le niveau
    d'urgence sont calculés par le backend.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    @field_validator(
        "description"
    )
    @classmethod
    def case_description_must_not_be_blank(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "La description "
                "ne peut pas être vide."
            )

        return value


class CasePublic(
    BaseModel
):
    """
    Représentation publique d'un dossier.

    user_id n'est pas exposé.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID

    detected_intent: (
        str | None
    )

    description: str

    language: (
        str | None
    )

    status: CaseStatus

    emergency: bool

    created_at: datetime

    updated_at: datetime