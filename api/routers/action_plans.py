"""
api/routers/action_plans.py

Persistance des plans d'action EMC Helpline.

Sécurité :
- routes réservées au rôle victim ;
- le dossier doit appartenir à la victime authentifiée ;
- le client n'envoie jamais la description ni le contenu du plan ;
- le plan est reconstruit côté serveur avec build_action_plan() ;
- toute modification est protégée par CSRF ;
- une victime ne peut ni lire ni modifier le plan d'une autre victime ;
- génération automatique des événements d'historique.
"""

import uuid

from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select

from sqlalchemy.exc import (
    IntegrityError,
)

from sqlalchemy.orm import (
    Session,
    selectinload,
)


from api.deps import (
    require_role,
    verify_csrf,
)


from db.action_plan_schemas import (
    ActionItemPublic,
    ActionItemUpdate,
    ActionPlanGenerateRequest,
    ActionPlanPublic,
)


from db.database import (
    get_db,
)


from db.models import (
    ActionItem,
    ActionPlan,
    Case,
    HistoryEvent,
    User,
    UserRole,
)


from rag.generator import (
    build_action_plan,
)


router = APIRouter(
    tags=["action-plans"],
)


# ============================================================
# HELPERS
# ============================================================

def _get_owned_case(

    case_id: uuid.UUID,

    current_user: User,

    db: Session,

) -> Case:

    stmt = (

        select(
            Case
        )

        .where(
            Case.id
            == case_id,

            Case.user_id
            == current_user.id,
        )
    )


    case = db.scalar(
        stmt
    )


    if case is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Dossier introuvable."
            ),
        )


    return case


def _load_plan_for_case(

    case_id: uuid.UUID,

    db: Session,

) -> ActionPlan | None:

    stmt = (

        select(
            ActionPlan
        )

        .options(
            selectinload(
                ActionPlan.items
            )
        )

        .where(
            ActionPlan.case_id
            == case_id
        )
    )


    return db.scalar(
        stmt
    )


# ============================================================
# GENERATE + SAVE ACTION PLAN
# ============================================================

@router.post(
    "/cases/{case_id}/action-plan",
    response_model=ActionPlanPublic,
)
def generate_and_save_action_plan(

    case_id: uuid.UUID,

    payload: ActionPlanGenerateRequest,

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    _: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),

) -> ActionPlanPublic:

    """
    Génère puis persiste le plan d'action.

    Si un plan existe déjà, il est renvoyé
    sans générer un nouvel événement.
    """

    # ========================================================
    # OWNERSHIP
    # ========================================================

    case = _get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )


    # ========================================================
    # IDEMPOTENCE
    # ========================================================

    existing_plan = (
        _load_plan_for_case(
            case_id=case.id,
            db=db,
        )
    )


    if (
        existing_plan
        is not None
    ):

        return existing_plan


    # ========================================================
    # BUILD ACTION PLAN
    # ========================================================

    try:

        result = build_action_plan(

            question=(
                case.description
            ),

            age_status=(
                payload
                .age_at_time_of_facts
            ),
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc


    except RuntimeError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Le service de construction "
                "du plan d'action est "
                "momentanément indisponible."
            ),
        ) from exc


    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Une erreur interne est survenue "
                "lors de la construction "
                "du plan d'action."
            ),
        ) from exc


    actions = (
        result.get(
            "actions",
            [],
        )
    )


    if (
        result.get("outcome")
        != "ready"

        or not isinstance(
            actions,
            list,
        )

        or len(actions) == 0
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Le plan d'action n'est pas "
                "encore prêt. Une clarification "
                "peut être nécessaire."
            ),
        )


    # ========================================================
    # CREATE PLAN
    # ========================================================

    plan = ActionPlan(

        case_id=case.id,

        language=(
            result.get(
                "language"
            )
            or case.language
            or "fr"
        ),

        detected_intent=(
            result.get(
                "predicted_intent"
            )
            or case.detected_intent
        ),
    )


    # ========================================================
    # ACTION ITEMS
    # ========================================================

    for index, action in enumerate(
        actions,
        start=1,
    ):

        plan.items.append(

            ActionItem(

                source_action_id=str(
                    action.get(
                        "id",
                        index,
                    )
                ),

                position=index,

                title=str(
                    action.get(
                        "title",
                        "",
                    )
                ),

                description=str(
                    action.get(
                        "description",
                        "",
                    )
                ),

                evidence=str(
                    action.get(
                        "evidence",
                        "",
                    )
                ),

                source=(
                    action.get(
                        "source"
                    )

                    if isinstance(
                        action.get(
                            "source"
                        ),
                        dict,
                    )

                    else None
                ),

                completed=False,
            )
        )


    # ========================================================
    # SAVE PLAN + HISTORY
    # ========================================================

    db.add(
        plan
    )


    try:

        # Génère plan.id sans commit.
        db.flush()


        history_event = (
            HistoryEvent(

                case_id=case.id,

                actor_user_id=(
                    current_user.id
                ),

                event_type=(
                    "action_plan_generated"
                ),

                event_data={

                    "action_plan_id":
                        str(plan.id),

                    "actions_count":
                        len(actions),

                    "detected_intent":
                        plan.detected_intent,

                    "language":
                        plan.language,
                },
            )
        )


        db.add(
            history_event
        )


        db.commit()


    except IntegrityError:

        # Cas de deux requêtes concurrentes.
        db.rollback()


        existing_plan = (
            _load_plan_for_case(
                case_id=case.id,
                db=db,
            )
        )


        if (
            existing_plan
            is not None
        ):

            return existing_plan


        raise


    except Exception:

        db.rollback()

        raise


    # ========================================================
    # RELOAD
    # ========================================================

    persisted_plan = (
        _load_plan_for_case(
            case_id=case.id,
            db=db,
        )
    )


    if (
        persisted_plan
        is None
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Le plan a été créé mais "
                "n'a pas pu être relu."
            ),
        )


    return persisted_plan


# ============================================================
# GET PLAN FOR CASE
# ============================================================

@router.get(
    "/cases/{case_id}/action-plan",
    response_model=ActionPlanPublic,
)
def get_case_action_plan(

    case_id: uuid.UUID,

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    db: Session = Depends(
        get_db
    ),

) -> ActionPlanPublic:

    case = _get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )


    plan = _load_plan_for_case(
        case_id=case.id,
        db=db,
    )


    if plan is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Plan d'action introuvable."
            ),
        )


    return plan


# ============================================================
# GET LATEST ACTION PLAN
# ============================================================

@router.get(
    "/action-plans/latest",
    response_model=ActionPlanPublic,
)
def get_latest_action_plan(

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    db: Session = Depends(
        get_db
    ),

) -> ActionPlanPublic:

    stmt = (

        select(
            ActionPlan
        )

        .join(
            Case,
            Case.id
            == ActionPlan.case_id,
        )

        .options(
            selectinload(
                ActionPlan.items
            )
        )

        .where(
            Case.user_id
            == current_user.id
        )

        .order_by(
            ActionPlan.created_at.desc()
        )

        .limit(1)
    )


    plan = db.scalar(
        stmt
    )


    if plan is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Aucun plan d'action enregistré."
            ),
        )


    return plan


# ============================================================
# UPDATE ACTION ITEM
# ============================================================

@router.patch(
    "/action-items/{item_id}",
    response_model=ActionItemPublic,
)
def update_action_item(

    item_id: uuid.UUID,

    payload: ActionItemUpdate,

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    _: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),

) -> ActionItemPublic:

    """
    Coche ou décoche une action.

    Si l'état change réellement :
    - action_completed
    - action_reopened
    est ajouté à l'historique.
    """

    # ========================================================
    # OWNERSHIP
    # ========================================================

    stmt = (

        select(
            ActionItem
        )

        .join(
            ActionPlan,
            ActionPlan.id
            == ActionItem.action_plan_id,
        )

        .join(
            Case,
            Case.id
            == ActionPlan.case_id,
        )

        .where(
            ActionItem.id
            == item_id,

            Case.user_id
            == current_user.id,
        )
    )


    item = db.scalar(
        stmt
    )


    if item is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Action introuvable."
            ),
        )


    # ========================================================
    # PREVIOUS STATE
    # ========================================================

    previous_completed = (
        item.completed
    )


    # ========================================================
    # UPDATE
    # ========================================================

    item.completed = (
        payload.completed
    )


    item.completed_at = (

        datetime.now(
            timezone.utc
        )

        if payload.completed

        else None
    )


    # ========================================================
    # PLAN
    # ========================================================

    plan = db.get(
        ActionPlan,
        item.action_plan_id,
    )


    if plan is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Plan d'action introuvable."
            ),
        )


    now = datetime.now(
        timezone.utc
    )


    plan.updated_at = (
        now
    )


    # ========================================================
    # HISTORY ONLY IF STATE CHANGED
    # ========================================================

    if (
        previous_completed
        != payload.completed
    ):

        event_type = (

            "action_completed"

            if payload.completed

            else "action_reopened"
        )


        history_event = (
            HistoryEvent(

                case_id=(
                    plan.case_id
                ),

                actor_user_id=(
                    current_user.id
                ),

                event_type=(
                    event_type
                ),

                event_data={

                    "action_item_id":
                        str(item.id),

                    "action_plan_id":
                        str(plan.id),

                    "title":
                        item.title,

                    "position":
                        item.position,

                    "completed":
                        payload.completed,
                },
            )
        )


        db.add(
            history_event
        )


    try:

        db.commit()

        db.refresh(
            item
        )


    except Exception:

        db.rollback()

        raise


    return item