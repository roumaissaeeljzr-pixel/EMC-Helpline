from datetime import date

from pydantic import BaseModel


class AdminStatisticsCountItem(BaseModel):
    label: str
    count: int
    percentage: float


class AdminStatisticsDailyPoint(BaseModel):
    date: date
    count: int


class AdminStatisticsSummary(BaseModel):
    total_cases: int
    active_cases: int
    closed_cases: int
    emergency_cases: int
    active_emergency_cases: int

    total_victims: int
    active_victims: int
    total_evidence: int
    total_action_plans: int

    total_action_items: int
    completed_action_items: int
    action_completion_rate: float

    period_cases: int
    previous_period_cases: int
    period_change_percent: float | None = None


class AdminStatisticsPublic(BaseModel):
    period_days: int

    summary: AdminStatisticsSummary

    daily_cases: list[AdminStatisticsDailyPoint]
    by_intent: list[AdminStatisticsCountItem]
    by_language: list[AdminStatisticsCountItem]
    by_status: list[AdminStatisticsCountItem]
    by_evidence_type: list[AdminStatisticsCountItem]