"""
api/routers/admin_statistics.py

Statistiques administrateur EMC Helpline.

Les données exposées sont agrégées.
Aucune description de dossier, preuve, adresse e-mail ou donnée privée
d'une victime n'est retournée par cet endpoint.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from sqlalchemy import (
    Date,
    cast,
    func,
    select,
)

from sqlalchemy.orm import Session

from api.deps import require_role

from db.admin_statistics_schemas import (
    AdminStatisticsCountItem,
    AdminStatisticsDailyPoint,
    AdminStatisticsPublic,
    AdminStatisticsSummary,
)

from db.database import get_db

from db.models import (
    ActionItem,
    ActionPlan,
    Case,
    CaseStatus,
    Evidence,
    User,
    UserRole,
)


router = APIRouter(
    tags=["admin-statistics"],
)


def scalar_count(
    db: Session,
    statement,
) -> int:
    value = db.scalar(statement)
    return int(value or 0)


def enum_value(value) -> str:
    if hasattr(value, "value"):
        return str(value.value)

    return str(value)


def percentage(
    count: int,
    total: int,
) -> float:
    if total <= 0:
        return 0.0

    return round(
        (count / total) * 100,
        1,
    )


@router.get(
    "/admin/statistics",
    response_model=AdminStatisticsPublic,
)
def get_admin_statistics(
    days: int = Query(
        default=30,
        ge=7,
        le=365,
    ),
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminStatisticsPublic:

    # ========================================================
    # PÉRIODES
    # ========================================================

    now = datetime.now(
        timezone.utc
    )

    current_start = (
        now
        - timedelta(
            days=days - 1
        )
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    previous_start = (
        current_start
        - timedelta(
            days=days
        )
    )

    # ========================================================
    # RÉSUMÉ GLOBAL
    # ========================================================

    total_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ),
    )

    active_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.status
            == CaseStatus.active
        ),
    )

    closed_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.status
            == CaseStatus.closed
        ),
    )

    emergency_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.emergency.is_(True)
        ),
    )

    active_emergency_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.emergency.is_(True),
            Case.status == CaseStatus.active,
        ),
    )

    total_victims = scalar_count(
        db,
        select(
            func.count(User.id)
        ).where(
            User.role
            == UserRole.victim
        ),
    )

    active_victims = scalar_count(
        db,
        select(
            func.count(User.id)
        ).where(
            User.role == UserRole.victim,
            User.is_active.is_(True),
        ),
    )

    total_evidence = scalar_count(
        db,
        select(
            func.count(Evidence.id)
        ),
    )

    total_action_plans = scalar_count(
        db,
        select(
            func.count(ActionPlan.id)
        ),
    )

    total_action_items = scalar_count(
        db,
        select(
            func.count(ActionItem.id)
        ),
    )

    completed_action_items = scalar_count(
        db,
        select(
            func.count(ActionItem.id)
        ).where(
            ActionItem.completed.is_(True)
        ),
    )

    action_completion_rate = percentage(
        completed_action_items,
        total_action_items,
    )

    # ========================================================
    # COMPARAISON PÉRIODE
    # ========================================================

    period_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.created_at
            >= current_start
        ),
    )

    previous_period_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.created_at
            >= previous_start,
            Case.created_at
            < current_start,
        ),
    )

    if previous_period_cases > 0:
        period_change_percent = round(
            (
                (
                    period_cases
                    - previous_period_cases
                )
                / previous_period_cases
            )
            * 100,
            1,
        )
    elif period_cases > 0:
        # Aucune base de comparaison : afficher "Nouvelle activité"
        # côté frontend plutôt qu'un +100 % trompeur.
        period_change_percent = None
    else:
        period_change_percent = 0.0

    # ========================================================
    # COURBE JOURNALIÈRE
    # ========================================================

    day_expression = cast(
        Case.created_at,
        Date,
    )

    daily_rows = db.execute(
        select(
            day_expression,
            func.count(Case.id),
        )
        .where(
            Case.created_at
            >= current_start
        )
        .group_by(
            day_expression
        )
        .order_by(
            day_expression.asc()
        )
    ).all()

    daily_map = {
        row_date:
            int(count)
        for row_date, count
        in daily_rows
    }

    daily_cases = []

    for offset in range(days):
        current_date = (
            current_start.date()
            + timedelta(
                days=offset
            )
        )

        daily_cases.append(
            AdminStatisticsDailyPoint(
                date=current_date,
                count=daily_map.get(
                    current_date,
                    0,
                ),
            )
        )

    # ========================================================
    # INTENTIONS
    # ========================================================

    intent_rows = db.execute(
        select(
            Case.detected_intent,
            func.count(Case.id),
        )
        .where(
            Case.detected_intent
            .is_not(None)
        )
        .group_by(
            Case.detected_intent
        )
        .order_by(
            func.count(Case.id)
            .desc()
        )
    ).all()

    intent_total = sum(
        int(count)
        for _, count
        in intent_rows
    )

    by_intent = [
        AdminStatisticsCountItem(
            label=str(label),
            count=int(count),
            percentage=percentage(
                int(count),
                intent_total,
            ),
        )
        for label, count
        in intent_rows
        if label
    ]

    # ========================================================
    # LANGUES
    # ========================================================

    language_rows = db.execute(
        select(
            Case.language,
            func.count(Case.id),
        )
        .where(
            Case.language
            .is_not(None)
        )
        .group_by(
            Case.language
        )
        .order_by(
            func.count(Case.id)
            .desc()
        )
    ).all()

    language_total = sum(
        int(count)
        for _, count
        in language_rows
    )

    by_language = [
        AdminStatisticsCountItem(
            label=str(label),
            count=int(count),
            percentage=percentage(
                int(count),
                language_total,
            ),
        )
        for label, count
        in language_rows
        if label
    ]

    # ========================================================
    # STATUTS
    # ========================================================

    status_rows = db.execute(
        select(
            Case.status,
            func.count(Case.id),
        )
        .group_by(
            Case.status
        )
        .order_by(
            func.count(Case.id)
            .desc()
        )
    ).all()

    status_total = sum(
        int(count)
        for _, count
        in status_rows
    )

    by_status = [
        AdminStatisticsCountItem(
            label=enum_value(label),
            count=int(count),
            percentage=percentage(
                int(count),
                status_total,
            ),
        )
        for label, count
        in status_rows
    ]

    # ========================================================
    # TYPES DE PREUVES
    # ========================================================

    evidence_rows = db.execute(
        select(
            Evidence.type,
            func.count(Evidence.id),
        )
        .group_by(
            Evidence.type
        )
        .order_by(
            func.count(Evidence.id)
            .desc()
        )
    ).all()

    evidence_total = sum(
        int(count)
        for _, count
        in evidence_rows
    )

    by_evidence_type = [
        AdminStatisticsCountItem(
            label=enum_value(label),
            count=int(count),
            percentage=percentage(
                int(count),
                evidence_total,
            ),
        )
        for label, count
        in evidence_rows
    ]

    # ========================================================
    # RESPONSE
    # ========================================================

    return AdminStatisticsPublic(
        period_days=days,

        summary=AdminStatisticsSummary(
            total_cases=total_cases,
            active_cases=active_cases,
            closed_cases=closed_cases,
            emergency_cases=emergency_cases,
            active_emergency_cases=active_emergency_cases,

            total_victims=total_victims,
            active_victims=active_victims,
            total_evidence=total_evidence,
            total_action_plans=total_action_plans,

            total_action_items=total_action_items,
            completed_action_items=completed_action_items,
            action_completion_rate=action_completion_rate,

            period_cases=period_cases,
            previous_period_cases=previous_period_cases,
            period_change_percent=period_change_percent,
        ),

        daily_cases=daily_cases,
        by_intent=by_intent,
        by_language=by_language,
        by_status=by_status,
        by_evidence_type=by_evidence_type,
    )