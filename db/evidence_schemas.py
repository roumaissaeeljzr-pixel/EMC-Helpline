"""
db/evidence_schemas.py

Schémas Pydantic pour le module "Mes preuves".
"""

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
)


# ============================================================
# LINK
# ============================================================

class EvidenceLinkCreate(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    url: HttpUrl


# ============================================================
# NOTE
# ============================================================

class EvidenceNoteCreate(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    note: str = Field(
        ...,
        min_length=1,
        max_length=20000,
    )


# ============================================================
# PUBLIC RESPONSE
# ============================================================

class EvidencePublic(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID

    case_id: uuid.UUID

    type: str

    title: str

    original_filename: str | None = None

    mime_type: str | None = None

    file_size: int | None = None

    sha256: str | None = None

    url: str | None = None

    note: str | None = None

    created_at: datetime

    updated_at: datetime