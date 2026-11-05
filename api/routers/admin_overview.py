"""
api/routers/admin_overview.py

Vue générale administrateur EMC Helpline.

Cette route retourne uniquement des données agrégées ou techniques.
Elle n'expose pas :
- les descriptions complètes des victimes ;
- le contenu des preuves ;
- les e-mails ;
- les mots de passe ;
- les données privées des dossiers.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy import (
    Date,
    cast,
    func,
    select,
)

from sqlalchemy.orm import Session

from api.deps import require_role

from db.admin_overview_schemas import (
    AdminOverviewCountItem,
    AdminOverviewDailyCount,
    AdminOverviewPriorityCase,
    AdminOverviewPublic,
    AdminOverviewRecentActivity,
    AdminOverviewSummary,
)

from db.database import get_db

from db.models import (
    ActionItem,
    ActionPlan,
    Case,
    CaseStatus,
    Evidence,
    HistoryEvent,
    Resource,
    User,
    UserRole,
)


router = APIRouter(
    tags=["admin-overview"],
)


def scalar_count(
    db: Session,
    statement,
) -> int:
    value = db.scalar(statement)

    return int(
        value or 0
    )


@router.get(
    "/admin/overview",
    response_model=AdminOverviewPublic,
)
def get_admin_overview(
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminOverviewPublic:

    # ========================================================
    # PÉRIODE
    # ========================================================

    now = datetime.now(
        timezone.utc
    )

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    first_day = (
        today_start
        - timedelta(days=6)
    )

    # ========================================================
    # UTILISATEURS
    # ========================================================

    victims = scalar_count(
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
            User.role
            == UserRole.victim,
            User.is_active.is_(True),
        ),
    )

    # ========================================================
    # DOSSIERS
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

    # "Cas prioritaires" = urgences encore actives.
    priority_cases = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.status
            == CaseStatus.active,
            Case.emergency.is_(True),
        ),
    )

    new_cases_today = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.created_at
            >= today_start
        ),
    )

    new_cases_last_7_days = scalar_count(
        db,
        select(
            func.count(Case.id)
        ).where(
            Case.created_at
            >= first_day
        ),
    )

    # ========================================================
    # PREUVES
    # ========================================================

    total_evidence = scalar_count(
        db,
        select(
            func.count(Evidence.id)
        ),
    )

    # ========================================================
    # PLANS D'ACTION
    # ========================================================

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

    action_completion_rate = (
        round(
            (
                completed_action_items
                / total_action_items
            )
            * 100,
            1,
        )
        if total_action_items > 0
        else 0.0
    )

    # ========================================================
    # RESSOURCES
    # ========================================================

    published_resources = scalar_count(
        db,
        select(
            func.count(Resource.id)
        ).where(
            Resource.status
            == "published"
        ),
    )

    draft_resources = scalar_count(
        db,
        select(
            func.count(Resource.id)
        ).where(
            Resource.status
            == "draft"
        ),
    )

    # ========================================================
    # RÉPARTITION PAR INTENTION
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
        .limit(6)
    ).all()

    by_intent = [
        AdminOverviewCountItem(
            label=str(label),
            count=int(count),
        )
        for label, count
        in intent_rows
        if label
    ]

    # ========================================================
    # RÉPARTITION FR / AR
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

    by_language = [
        AdminOverviewCountItem(
            label=str(label),
            count=int(count),
        )
        for label, count
        in language_rows
        if label
    ]

    # ========================================================
    # DOSSIERS — 7 DERNIERS JOURS
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
            >= first_day
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

    cases_last_7_days = []

    for offset in range(7):
        current_date = (
            first_day.date()
            + timedelta(
                days=offset
            )
        )

        cases_last_7_days.append(
            AdminOverviewDailyCount(
                date=current_date,
                count=daily_map.get(
                    current_date,
                    0,
                ),
            )
        )

    # ========================================================
    # ACTIVITÉ RÉCENTE
    # ========================================================

    recent_rows = db.execute(
        select(
            HistoryEvent.event_type,
            HistoryEvent.created_at,
            Case.detected_intent,
        )
        .join(
            Case,
            Case.id
            == HistoryEvent.case_id,
        )
        .order_by(
            HistoryEvent.created_at
            .desc()
        )
        .limit(8)
    ).all()

    recent_activity = [
        AdminOverviewRecentActivity(
            event_type=event_type,
            created_at=created_at,
            detected_intent=detected_intent,
        )
        for (
            event_type,
            created_at,
            detected_intent,
        )
        in recent_rows
    ]

    # ========================================================
    # CAS PRIORITAIRES
    # ========================================================

    priority_rows = db.execute(
        select(
            Case.detected_intent,
            Case.status,
            Case.created_at,
            Case.updated_at,
        )
        .where(
            Case.status
            == CaseStatus.active,
            Case.emergency.is_(True),
        )
        .order_by(
            Case.updated_at.desc()
        )
        .limit(5)
    ).all()

    priority_case_items = [
        AdminOverviewPriorityCase(
            detected_intent=(
                detected_intent
            ),
            status=(
                status.value
                if hasattr(
                    status,
                    "value",
                )
                else str(status)
            ),
            created_at=created_at,
            updated_at=updated_at,
        )
        for (
            detected_intent,
            status,
            created_at,
            updated_at,
        )
        in priority_rows
    ]

    # ========================================================
    # RESPONSE
    # ========================================================

    return AdminOverviewPublic(
        summary=AdminOverviewSummary(
            victims=victims,
            active_victims=active_victims,

            total_cases=total_cases,
            active_cases=active_cases,
            closed_cases=closed_cases,
            priority_cases=priority_cases,

            total_evidence=total_evidence,

            total_action_plans=(
                total_action_plans
            ),
            total_action_items=(
                total_action_items
            ),
            completed_action_items=(
                completed_action_items
            ),
            action_completion_rate=(
                action_completion_rate
            ),

            published_resources=(
                published_resources
            ),
            draft_resources=(
                draft_resources
            ),

            new_cases_today=(
                new_cases_today
            ),
            new_cases_last_7_days=(
                new_cases_last_7_days
            ),
        ),

        by_intent=by_intent,
        by_language=by_language,

        cases_last_7_days=(
            cases_last_7_days
        ),

        recent_activity=(
            recent_activity
        ),

        priority_cases=(
            priority_case_items
        ),
    )