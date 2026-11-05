import uuid

from typing import Literal

from pydantic import BaseModel


class CaseDeletionStatus(
    BaseModel
):
    case_id: uuid.UUID

    viewed_by_admin: bool

    deletion_requested: bool

    mode: Literal[
        "delete_immediately",
        "request_required",
        "request_pending",
    ]


class CaseDeletionResult(
    BaseModel
):
    case_id: uuid.UUID

    outcome: Literal[
        "deleted",
        "request_submitted",
        "request_already_pending",
    ]

    message: str
