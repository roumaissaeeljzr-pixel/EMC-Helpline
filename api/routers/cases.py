"""
api/routers/cases.py

Routes des dossiers personnels d'une victime authentifiée.

Sécurité :
- accès réservé au rôle victim ;
- aucune route ne prend user_id depuis le client ;
- toutes les lectures filtrent par current_user.id ;
- POST protégé par CSRF ;
- les métadonnées IA sont calculées côté serveur ;
- création automatique d'un événement d'historique ;
- suppression contrôlée :
  * dossier jamais consulté par l'équipe EMC -> suppression définitive ;
  * dossier déjà consulté -> demande de suppression enregistrée ;
- nettoyage des fichiers de preuve après suppression réussie.
"""

import logging
import uuid

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import (
    require_role,
    verify_csrf,
)

from db.database import get_db

from db.models import (
    Case,
    CaseStatus,
    Evidence,
    HistoryEvent,
    User,
    UserRole,
)

from db.schemas import (
    CaseCreate,
    CasePublic,
)

from db.case_deletion_schemas import (
    CaseDeletionResult,
    CaseDeletionStatus,
)

from rag.generator import (
    classify_situation,
)


router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)


logger = logging.getLogger(
    __name__
)


def _load_owned_case(
    *,
    case_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Case:
    case = db.scalar(
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


def _has_history_event(
    *,
    case_id: uuid.UUID,
    event_type: str,
    db: Session,
) -> bool:
    event_id = db.scalar(
        select(
            HistoryEvent.id
        )
        .where(
            HistoryEvent.case_id
            == case_id,
            HistoryEvent.event_type
            == event_type,
        )
        .limit(1)
    )

    return (
        event_id is not None
    )


def _latest_deletion_event_type(
    *,
    case_id: uuid.UUID,
    db: Session,
) -> str | None:
    event_type = db.scalar(
        select(
            HistoryEvent.event_type
        )
        .where(
            HistoryEvent.case_id == case_id,
            HistoryEvent.event_type.in_(
                [
                    "case_deletion_requested",
                    "case_deletion_rejected",
                ]
            ),
        )
        .order_by(
            HistoryEvent.created_at.desc(),
            HistoryEvent.id.desc(),
        )
        .limit(1)
    )

    return str(event_type) if event_type else None


def _collect_evidence_files(
    *,
    case_id: uuid.UUID,
    db: Session,
) -> list[
    tuple[
        uuid.UUID,
        Path,
    ]
]:
    rows = db.execute(
        select(
            Evidence.id,
            Evidence.storage_path,
        )
        .where(
            Evidence.case_id
            == case_id,
            Evidence.storage_path
            .is_not(None),
        )
    ).all()

    files = []

    for (
        evidence_id,
        storage_path,
    ) in rows:
        if not storage_path:
            continue

        files.append(
            (
                evidence_id,
                Path(
                    storage_path
                ),
            )
        )

    return files


def _cleanup_evidence_files(
    files: list[
        tuple[
            uuid.UUID,
            Path,
        ]
    ],
) -> None:
    for (
        evidence_id,
        path,
    ) in files:
        try:
            path.unlink(
                missing_ok=True
            )
        except OSError:
            logger.warning(
                (
                    "Impossible de nettoyer le fichier "
                    "d'une preuve supprimée. evidence_id=%s"
                ),
                evidence_id,
            )


# ============================================================
# CREATE CASE
# ============================================================

@router.post(
    "",
    response_model=CasePublic,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    payload: CaseCreate,

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
) -> CasePublic:

    """
    Crée un dossier appartenant exclusivement
    à la victime connectée.

    user_id n'est jamais accepté depuis le client.

    Lors de la création du dossier,
    un événement case_created est également
    enregistré dans history_events.
    """

    # ========================================================
    # CLASSIFICATION IA
    # ========================================================

    try:

        classification = (
            classify_situation(
                payload.description
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Une erreur interne est survenue "
                "lors de l'analyse de la situation."
            ),
        ) from exc


    # ========================================================
    # CRÉATION DU DOSSIER
    # ========================================================

    case = Case(

        user_id=current_user.id,

        description=(
            payload.description
        ),

        detected_intent=(
            classification.get(
                "predicted_intent"
            )
        ),

        language=(
            classification.get(
                "language"
            )
        ),

        emergency=(
            classification.get(
                "emergency_override",
                False,
            )
        ),

        status=CaseStatus.active,
    )


    try:

        db.add(
            case
        )

        # Nécessaire pour obtenir case.id
        # avant le commit.
        db.flush()


        # ====================================================
        # HISTORY : CASE CREATED
        # ====================================================

        history_event = (
            HistoryEvent(

                case_id=case.id,

                actor_user_id=(
                    current_user.id
                ),

                event_type=(
                    "case_created"
                ),

                event_data={
                    "detected_intent":
                        case.detected_intent,

                    "language":
                        case.language,

                    "emergency":
                        case.emergency,

                    "status":
                        case.status.value,
                },
            )
        )


        db.add(
            history_event
        )


        # Le dossier et son événement sont
        # validés dans la même transaction.
        db.commit()


        db.refresh(
            case
        )


    except Exception:

        db.rollback()

        raise


    return case


# ============================================================
# LIST MY CASES
# ============================================================

@router.get(
    "",
    response_model=list[
        CasePublic
    ],
)
def list_my_cases(

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    db: Session = Depends(
        get_db
    ),

) -> list[CasePublic]:

    """
    Retourne uniquement les dossiers
    appartenant à la victime authentifiée.
    """

    stmt = (

        select(
            Case
        )

        .where(
            Case.user_id
            == current_user.id
        )

        .order_by(
            Case.created_at.desc()
        )
    )


    return list(
        db.scalars(
            stmt
        ).all()
    )


# ============================================================
# GET ONE CASE
# ============================================================

@router.get(
    "/{case_id}",
    response_model=CasePublic,
)
def get_my_case(

    case_id: uuid.UUID,

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    db: Session = Depends(
        get_db
    ),

) -> CasePublic:

    """
    Retourne le dossier uniquement
    s'il appartient à la victime connectée.

    Un dossier d'une autre victime retourne 404.
    """

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


# ============================================================
# CONTROLLED DELETION STATUS
# ============================================================

@router.get(
    "/{case_id}/deletion-status",
    response_model=CaseDeletionStatus,
)
def get_case_deletion_status(
    case_id: uuid.UUID,

    current_user: User = Depends(
        require_role(
            UserRole.victim
        )
    ),

    db: Session = Depends(
        get_db
    ),
) -> CaseDeletionStatus:
    """
    Indique si le dossier peut être supprimé immédiatement
    ou si une demande doit être transmise à l'équipe EMC.
    """

    case = _load_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    viewed_by_admin = _has_history_event(
        case_id=case.id,
        event_type=(
            "case_viewed_by_admin"
        ),
        db=db,
    )

    latest_deletion_event = (
        _latest_deletion_event_type(
            case_id=case.id,
            db=db,
        )
    )

    deletion_requested = (
        latest_deletion_event
        == "case_deletion_requested"
    )

    if deletion_requested:
        mode = (
            "request_pending"
        )
    elif viewed_by_admin:
        mode = (
            "request_required"
        )
    else:
        mode = (
            "delete_immediately"
        )

    return CaseDeletionStatus(
        case_id=case.id,
        viewed_by_admin=(
            viewed_by_admin
        ),
        deletion_requested=(
            deletion_requested
        ),
        mode=mode,
    )


# ============================================================
# CONTROLLED DELETION
# ============================================================

@router.post(
    "/{case_id}/deletion",
    response_model=CaseDeletionResult,
)
def delete_or_request_case_deletion(
    case_id: uuid.UUID,

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
) -> CaseDeletionResult:
    """
    Politique de suppression contrôlée :

    - jamais consulté par l'équipe EMC :
      suppression définitive du dossier ;
    - déjà consulté :
      demande de suppression enregistrée sans effacement immédiat.
    """

    case = _load_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )

    viewed_by_admin = _has_history_event(
        case_id=case.id,
        event_type=(
            "case_viewed_by_admin"
        ),
        db=db,
    )

    if viewed_by_admin:
        latest_deletion_event = (
            _latest_deletion_event_type(
                case_id=case.id,
                db=db,
            )
        )

        already_requested = (
            latest_deletion_event
            == "case_deletion_requested"
        )

        if already_requested:
            return CaseDeletionResult(
                case_id=case.id,
                outcome=(
                    "request_already_pending"
                ),
                message=(
                    "Une demande de suppression "
                    "est déjà en cours pour ce dossier."
                ),
            )

        request_event = HistoryEvent(
            case_id=case.id,
            actor_user_id=(
                current_user.id
            ),
            event_type=(
                "case_deletion_requested"
            ),
            event_data={
                "requested_by":
                    "victim",
                "requires_admin_review":
                    True,
            },
        )

        try:
            db.add(
                request_event
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

        return CaseDeletionResult(
            case_id=case.id,
            outcome=(
                "request_submitted"
            ),
            message=(
                "Votre demande de suppression "
                "a été transmise à l'équipe EMC."
            ),
        )

    evidence_files = _collect_evidence_files(
        case_id=case.id,
        db=db,
    )

    deleted_case_id = case.id

    try:
        db.delete(
            case
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    _cleanup_evidence_files(
        evidence_files
    )

    return CaseDeletionResult(
        case_id=deleted_case_id,
        outcome="deleted",
        message=(
            "Le dossier a été supprimé "
            "définitivement."
        ),
    )

