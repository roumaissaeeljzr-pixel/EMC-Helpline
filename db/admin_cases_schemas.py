import uuid
from datetime import (
    date,
    datetime,
)
from typing import Literal

from pydantic import BaseModel


class AdminCasesSummary(BaseModel):
    total_cases: int
    active_cases: int
    closed_cases: int
    priority_cases: int


class AdminEvidenceListItem(BaseModel):
    id: uuid.UUID
    type: str
    title: str

    original_filename: str | None = None
    mime_type: str | None = None
    file_size: int | None = None

    created_at: datetime


class AdminEvidenceDetail(AdminEvidenceListItem):
    url: str | None = None
    note: str | None = None

    has_download: bool = False


class AdminCaseListItem(BaseModel):
    id: uuid.UUID

    victim_username: str
    victim_full_name: str | None = None
    victim_emc_id: str
    victim_phone: str | None = None
    victim_cin_masked: str | None = None
    victim_identity_complete: bool = False

    deletion_requested: bool = False
    deletion_request_status: str = "none"

    detected_intent: str | None = None
    language: str | None = None
    status: str
    workflow_status: str
    emergency: bool

    evidence_count: int
    has_action_plan: bool
    total_actions: int
    completed_actions: int
    action_progress: float

    created_at: datetime
    updated_at: datetime


class AdminCaseDetail(AdminCaseListItem):
    victim_email: str | None = None
    victim_cin: str | None = None
    victim_date_of_birth: date | None = None

    description: str
    evidences: list[AdminEvidenceListItem]


class AdminCasesPublic(BaseModel):
    summary: AdminCasesSummary
    items: list[AdminCaseListItem]
    filtered_count: int
    intents: list[str]


class AdminCaseWorkflowStatusUpdate(BaseModel):
    workflow_status: Literal[
        "new",
        "in_progress",
        "waiting_information",
        "resolved",
        "closed",
    ]


class AdminCaseStatusUpdate(BaseModel):
    status: Literal[
        "active",
        "closed",
    ]


class AdminDeletionRequestDecision(BaseModel):
    decision: Literal[
        "approve",
        "reject",
    ]


class AdminDeletionRequestResult(BaseModel):
    case_id: uuid.UUID
    outcome: Literal[
        "deleted",
        "rejected",
    ]
    message: str
