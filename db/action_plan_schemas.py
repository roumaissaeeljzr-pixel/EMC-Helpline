"""
db/action_plan_schemas.py

Schémas Pydantic dédiés aux plans d'action persistants.
Séparés de db/schemas.py pour ne pas modifier les schémas
d'authentification et de dossiers déjà validés.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ActionPlanGenerateRequest(BaseModel):
    """
    Paramètres nécessaires pour générer le plan d'un dossier existant.

    La description, l'utilisateur et l'intention ne viennent jamais
    du client : le backend les récupère depuis le Case appartenant à
    la victime authentifiée.
    """

    model_config = ConfigDict(extra="forbid")

    age_at_time_of_facts: Literal[
        "minor",
        "adult",
    ] | None = None


class ActionItemUpdate(BaseModel):
    """Modification de l'état d'avancement d'une action."""

    model_config = ConfigDict(extra="forbid")

    completed: bool


class ActionItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_action_id: str
    position: int
    title: str
    description: str
    completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ActionPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    language: str
    detected_intent: str | None
    created_at: datetime
    updated_at: datetime

    # L'ORM appelle la relation "items", mais l'API conserve
    # le nom "actions" utilisé par le frontend existant.
    actions: list[ActionItemPublic] = Field(
        default_factory=list,
        validation_alias="items",
    )