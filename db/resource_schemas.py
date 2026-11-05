"""
db/resource_schemas.py

Schémas Pydantic du module Ressources EMC Helpline.

Les modèles SQLAlchemy restent dans db/models.py.
Ces schémas servent uniquement à valider les requêtes HTTP
et à contrôler ce qui est exposé par l'API.

FR + arabe standard uniquement.
"""

import uuid

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ============================================================
# TYPES AUTORISÉS
# ============================================================

ResourceCategory = Literal[
    "account",
    "evidence",
    "harassment",
    "privacy",
    "identity",
    "images",
    "legal",
    "report",
    "emergency",
    "support",
]


ResourceStatus = Literal[
    "draft",
    "published",
]


ResourceTone = Literal[
    "purple",
    "blue",
    "green",
    "pink",
    "orange",
    "coral",
]


# ============================================================
# HELPERS
# ============================================================

def _clean_text(
    value: str,
) -> str:
    value = value.strip()

    if not value:
        raise ValueError(
            "La valeur ne peut pas être vide."
        )

    return value


def _clean_points(
    values: list[str],
) -> list[str]:
    cleaned: list[str] = []

    for item in values:
        if not isinstance(
            item,
            str,
        ):
            raise ValueError(
                "Chaque point doit être une chaîne de caractères."
            )

        item = item.strip()

        if not item:
            continue

        if len(item) > 1000:
            raise ValueError(
                "Un point ne peut pas dépasser 1000 caractères."
            )

        cleaned.append(
            item
        )

    if len(cleaned) > 30:
        raise ValueError(
            "Une ressource ne peut pas contenir plus de 30 points."
        )

    return cleaned


# ============================================================
# CREATE
# ============================================================

class ResourceCreate(BaseModel):
    """
    Création d'une ressource par un administrateur.

    created_by n'est jamais envoyé par le client.
    Il provient de l'admin authentifié.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    category: ResourceCategory

    title_fr: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    title_ar: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description_fr: str = Field(
        ...,
        min_length=1,
        max_length=3000,
    )

    description_ar: str = Field(
        ...,
        min_length=1,
        max_length=3000,
    )

    content_fr: str | None = Field(
        default=None,
        max_length=30000,
    )

    content_ar: str | None = Field(
        default=None,
        max_length=30000,
    )

    points_fr: list[str] = Field(
        default_factory=list,
    )

    points_ar: list[str] = Field(
        default_factory=list,
    )

    icon: str | None = Field(
        default=None,
        max_length=50,
    )

    tone: ResourceTone | None = None

    status: ResourceStatus = "draft"

    display_order: int = Field(
        default=0,
        ge=0,
        le=100000,
    )


    @field_validator(
        "title_fr",
        "title_ar",
        "description_fr",
        "description_ar",
    )
    @classmethod
    def required_text_must_not_be_blank(
        cls,
        value: str,
    ) -> str:
        return _clean_text(
            value
        )


    @field_validator(
        "content_fr",
        "content_ar",
        "icon",
    )
    @classmethod
    def optional_text_cleanup(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


    @field_validator(
        "points_fr",
        "points_ar",
    )
    @classmethod
    def points_cleanup(
        cls,
        values: list[str],
    ) -> list[str]:
        return _clean_points(
            values
        )


# ============================================================
# UPDATE
# ============================================================

class ResourceUpdate(BaseModel):
    """
    Modification partielle d'une ressource.

    Tous les champs sont optionnels pour permettre PATCH.
    Les champs obligatoires de la table ne peuvent toutefois pas
    être explicitement remplacés par null.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    category: ResourceCategory | None = None

    title_fr: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    title_ar: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description_fr: str | None = Field(
        default=None,
        min_length=1,
        max_length=3000,
    )

    description_ar: str | None = Field(
        default=None,
        min_length=1,
        max_length=3000,
    )

    content_fr: str | None = Field(
        default=None,
        max_length=30000,
    )

    content_ar: str | None = Field(
        default=None,
        max_length=30000,
    )

    points_fr: list[str] | None = None

    points_ar: list[str] | None = None

    icon: str | None = Field(
        default=None,
        max_length=50,
    )

    tone: ResourceTone | None = None

    status: ResourceStatus | None = None

    display_order: int | None = Field(
        default=None,
        ge=0,
        le=100000,
    )


    @field_validator(
        "title_fr",
        "title_ar",
        "description_fr",
        "description_ar",
    )
    @classmethod
    def update_text_cleanup(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return _clean_text(
            value
        )


    @field_validator(
        "content_fr",
        "content_ar",
        "icon",
    )
    @classmethod
    def update_optional_text_cleanup(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


    @field_validator(
        "points_fr",
        "points_ar",
    )
    @classmethod
    def update_points_cleanup(
        cls,
        values: list[str] | None,
    ) -> list[str] | None:
        if values is None:
            return None

        return _clean_points(
            values
        )


    @model_validator(
        mode="after"
    )
    def prevent_null_required_fields(
        self,
    ):
        required_fields = {
            "category",
            "title_fr",
            "title_ar",
            "description_fr",
            "description_ar",
            "points_fr",
            "points_ar",
            "status",
            "display_order",
        }

        for field_name in required_fields:
            if (
                field_name
                in self.model_fields_set
                and getattr(
                    self,
                    field_name,
                )
                is None
            ):
                raise ValueError(
                    f"{field_name} ne peut pas être null."
                )

        return self


# ============================================================
# RÉPONSE VICTIME
# ============================================================

class ResourcePublic(BaseModel):
    """
    Ressource visible côté victime.

    created_by n'est volontairement pas exposé.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID

    category: str

    title_fr: str
    title_ar: str

    description_fr: str
    description_ar: str

    content_fr: str | None
    content_ar: str | None

    points_fr: list
    points_ar: list

    icon: str | None
    tone: str | None

    status: str

    display_order: int

    created_at: datetime
    updated_at: datetime


# ============================================================
# RÉPONSE ADMIN
# ============================================================

class AdminResourcePublic(
    ResourcePublic
):
    """
    Version admin.

    L'admin peut également connaître l'identifiant
    de l'administrateur ayant créé la ressource.
    """

    created_by: uuid.UUID | None