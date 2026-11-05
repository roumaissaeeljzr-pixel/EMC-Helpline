"""
db/victim_profile_schemas.py
"""

import re
import uuid
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


NAME_PATTERN = re.compile(
    r"^[A-Za-zÀ-ÖØ-öø-ÿ\u0600-\u06FF '\-]{1,100}$"
)

PHONE_PATTERN = re.compile(
    r"^\+?[0-9][0-9 .\-]{7,19}$"
)

CIN_PATTERN = re.compile(
    r"^[A-Z0-9]{5,20}$"
)


def normalize_optional_text(
    value,
):
    if value is None:
        return None

    clean = str(
        value
    ).strip()

    return clean or None


class VictimProfileUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid"
    )

    first_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    date_of_birth: date | None = None

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    cin: str | None = Field(
        default=None,
        max_length=20,
    )

    @field_validator(
        "first_name",
        "last_name",
        mode="before",
    )
    @classmethod
    def validate_name(
        cls,
        value,
    ):
        clean = normalize_optional_text(
            value
        )

        if clean is None:
            return None

        if not NAME_PATTERN.fullmatch(
            clean
        ):
            raise ValueError(
                "Le nom contient des caractères non autorisés."
            )

        return clean

    @field_validator(
        "phone",
        mode="before",
    )
    @classmethod
    def validate_phone(
        cls,
        value,
    ):
        clean = normalize_optional_text(
            value
        )

        if clean is None:
            return None

        if not PHONE_PATTERN.fullmatch(
            clean
        ):
            raise ValueError(
                "Le numéro de téléphone n'est pas valide."
            )

        return clean

    @field_validator(
        "cin",
        mode="before",
    )
    @classmethod
    def validate_cin(
        cls,
        value,
    ):
        clean = normalize_optional_text(
            value
        )

        if clean is None:
            return None

        normalized = re.sub(
            r"[\s\-]+",
            "",
            clean,
        ).upper()

        if not CIN_PATTERN.fullmatch(
            normalized
        ):
            raise ValueError(
                "Format CIN invalide."
            )

        return normalized

    @field_validator(
        "date_of_birth",
    )
    @classmethod
    def validate_date_of_birth(
        cls,
        value,
    ):
        if value is None:
            return None

        today = date.today()

        if value >= today:
            raise ValueError(
                "La date de naissance doit être antérieure à aujourd'hui."
            )

        if (
            today.year
            - value.year
            > 120
        ):
            raise ValueError(
                "La date de naissance n'est pas valide."
            )

        return value


class VictimProfilePublic(BaseModel):
    user_id: uuid.UUID
    emc_id: str

    username: str
    email: str

    first_name: str | None
    last_name: str | None
    full_name: str | None

    date_of_birth: date | None
    phone: str | None

    # La victime peut voir sa propre CIN.
    cin: str | None
    cin_masked: str | None

    identity_complete: bool
    identity_completed_at: datetime | None

    created_at: datetime | None
    updated_at: datetime | None
