"""
api/routers/history.py

Lecture sécurisée de l'historique personnel EMC Helpline.

Endpoint :

GET /history
GET /history?case_id=<uuid>

Sécurité :
- victime authentifiée uniquement ;
- aucun user_id accepté depuis le client ;
- les événements sont toujours filtrés
  par current_user.id via le dossier ;
- une victime ne peut jamais lire
  l'historique d'une autre victime.
"""

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import (
    select,
)

from sqlalchemy.orm import (
    Session,
)

from api.deps import (
    require_role,
)

from db.database import (
    get_db,
)

from db.history_schemas import (
    HistoryEventPublic,
)

from db.models import (
    Case,
    HistoryEvent,
    User,
    UserRole,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/history",
    tags=["history"],
)


# ============================================================
# GET HISTORY
# ============================================================

@router.get(
    "",
    response_model=list[
        HistoryEventPublic
    ],
)
def get_my_history(

    case_id: (
        uuid.UUID
        | None
    ) = None,

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    db: Session = Depends(
        get_db
    ),

) -> list[HistoryEvent]:

    """
    Retourne l'historique de la victime.

    Sans case_id :
        retourne tous les événements
        appartenant à la victime.

    Avec case_id :
        retourne uniquement les événements
        du dossier demandé, après vérification
        de propriété.
    """

    # ========================================================
    # OPTIONAL CASE OWNERSHIP CHECK
    # ========================================================

    if case_id is not None:

        owned_case = db.scalar(

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


        if owned_case is None:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Dossier introuvable."
                ),
            )


    # ========================================================
    # BASE QUERY
    # ========================================================

    stmt = (

        select(
            HistoryEvent
        )

        .join(
            Case,
            Case.id
            == HistoryEvent.case_id,
        )

        .where(
            Case.user_id
            == current_user.id
        )
    )


    # ========================================================
    # OPTIONAL CASE FILTER
    # ========================================================

    if case_id is not None:

        stmt = stmt.where(
            HistoryEvent.case_id
            == case_id
        )


    # ========================================================
    # MOST RECENT FIRST
    # ========================================================

    stmt = stmt.order_by(
        HistoryEvent.created_at.desc()
    )


    events = list(
        db.scalars(
            stmt
        ).all()
    )


    return events