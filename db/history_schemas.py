"""
db/history_schemas.py

Schémas Pydantic publics pour l'historique EMC Helpline.
"""

import uuid

from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
)


class HistoryEventPublic(BaseModel):

    id: uuid.UUID

    case_id: uuid.UUID

    event_type: str

    event_data: (
        dict[str, Any]
        | None
    ) = None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )