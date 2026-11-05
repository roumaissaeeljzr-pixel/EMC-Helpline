from datetime import date, datetime

from pydantic import BaseModel


class AdminOverviewSummary(BaseModel):
    victims: int
    active_victims: int

    total_cases: int
    active_cases: int
    closed_cases: int
    priority_cases: int

    total_evidence: int

    total_action_plans: int
    total_action_items: int
    completed_action_items: int
    action_completion_rate: float

    published_resources: int
    draft_resources: int

    new_cases_today: int
    new_cases_last_7_days: int


class AdminOverviewCountItem(BaseModel):
    label: str
    count: int


class AdminOverviewDailyCount(BaseModel):
    date: date
    count: int


class AdminOverviewRecentActivity(BaseModel):
    event_type: str
    created_at: datetime
    detected_intent: str | None = None


class AdminOverviewPriorityCase(BaseModel):
    detected_intent: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class AdminOverviewPublic(BaseModel):
    summary: AdminOverviewSummary

    by_intent: list[AdminOverviewCountItem]
    by_language: list[AdminOverviewCountItem]

    cases_last_7_days: list[AdminOverviewDailyCount]

    recent_activity: list[AdminOverviewRecentActivity]
    priority_cases: list[AdminOverviewPriorityCase]