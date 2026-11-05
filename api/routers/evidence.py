"""
api/routers/evidence.py

API sécurisée du module "Mes preuves".

Routes :

POST   /cases/{case_id}/evidence/file
POST   /cases/{case_id}/evidence/link
POST   /cases/{case_id}/evidence/note

GET    /cases/{case_id}/evidence

GET    /evidence/{evidence_id}/download

DELETE /evidence/{evidence_id}

Sécurité :
- victime authentifiée uniquement ;
- vérification de propriété du dossier ;
- CSRF pour POST et DELETE ;
- fichiers dans un stockage non public ;
- noms de fichiers générés en UUID ;
- limite de taille ;
- liste blanche MIME ;
- SHA-256 ;
- aucun storage_path exposé au frontend ;
- historique automatique ajout/suppression.
"""

import hashlib
import uuid

from pathlib import Path


from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)


from fastapi.responses import (
    FileResponse,
)


from sqlalchemy.orm import (
    Session,
)


from api.deps import (
    get_current_user,
    verify_csrf,
)


from db.database import (
    get_db,
)


from db.evidence_schemas import (
    EvidenceLinkCreate,
    EvidenceNoteCreate,
    EvidencePublic,
)


from db.models import (
    Case,
    Evidence,
    EvidenceType,
    HistoryEvent,
    User,
    UserRole,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    tags=["evidence"],
)


# ============================================================
# STORAGE
# ============================================================

PROJECT_ROOT = (

    Path(__file__)
    .resolve()
    .parents[2]
)


PROTECTED_EVIDENCE_ROOT = (

    PROJECT_ROOT
    / "protected_storage"
    / "evidence"
)


# ============================================================
# LIMITES
# ============================================================

MAX_FILE_SIZE = (
    20
    * 1024
    * 1024
)


CHUNK_SIZE = (
    1024
    * 1024
)


# ============================================================
# MIME TYPES AUTORISÉS
# ============================================================

ALLOWED_MIME_TYPES = {

    # Images
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",

    # PDF
    "application/pdf",

    # Texte
    "text/plain",

    # Word
    "application/msword",

    (
        "application/"
        "vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    ),

    # Excel
    "application/vnd.ms-excel",

    (
        "application/"
        "vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),

    # Vidéo
    "video/mp4",
    "video/webm",
    "video/quicktime",

    # Audio
    "audio/mpeg",
    "audio/mp4",
    "audio/x-m4a",
    "audio/wav",
    "audio/x-wav",
}


# ============================================================
# HELPERS
# ============================================================

def _require_victim(
    current_user: User,
) -> None:

    if (
        current_user.role
        != UserRole.victim
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Accès réservé "
                "aux victimes."
            ),
        )


def _get_owned_case(
    *,
    case_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Case:

    case = (

        db.query(
            Case
        )

        .filter(
            Case.id
            == case_id,

            Case.user_id
            == current_user.id,
        )

        .first()
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


def _get_owned_evidence(
    *,
    evidence_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Evidence:

    evidence = (

        db.query(
            Evidence
        )

        .join(
            Case,
            Evidence.case_id
            == Case.id,
        )

        .filter(
            Evidence.id
            == evidence_id,

            Case.user_id
            == current_user.id,
        )

        .first()
    )


    if evidence is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Preuve introuvable."
            ),
        )


    return evidence


def _safe_original_filename(
    filename: str | None,
) -> str:

    if not filename:

        return "fichier"


    return (
        Path(
            filename
        )
        .name[:255]
    )


def _safe_extension(
    filename: str,
) -> str:

    suffix = (

        Path(
            filename
        )

        .suffix

        .lower()
    )


    if (
        len(suffix)
        > 12
    ):

        return ""


    return suffix


def _add_history_event(
    *,
    db: Session,
    case_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    event_type: str,
    event_data: dict | None,
) -> None:

    """
    Ajoute l'événement à la session courante.

    Aucun commit n'est effectué ici afin que
    l'action métier et son historique soient
    sauvegardés dans la même transaction.
    """

    event = HistoryEvent(

        case_id=(
            case_id
        ),

        actor_user_id=(
            actor_user_id
        ),

        event_type=(
            event_type
        ),

        event_data=(
            event_data
        ),
    )


    db.add(
        event
    )


# ============================================================
# FILE / SCREENSHOT UPLOAD
# ============================================================

@router.post(
    "/cases/{case_id}/evidence/file",
    response_model=EvidencePublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def upload_evidence_file(

    case_id: uuid.UUID,

    title: str = Form(...),

    evidence_type: str = Form(
        "file"
    ),

    file: UploadFile = File(...),

    current_user: User = Depends(
        get_current_user
    ),

    _csrf_checked: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),

) -> Evidence:

    """
    Types acceptés :
        file
        screenshot
    """

    _require_victim(
        current_user
    )


    case = _get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )


    # ========================================================
    # TITLE
    # ========================================================

    clean_title = (
        title.strip()
    )


    if (
        not clean_title

        or len(
            clean_title
        ) > 255
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Le titre est obligatoire "
                "et doit contenir au maximum "
                "255 caractères."
            ),
        )


    # ========================================================
    # EVIDENCE TYPE
    # ========================================================

    if evidence_type not in {
        "file",
        "screenshot",
    }:

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Type de preuve invalide."
            ),
        )


    evidence_enum = (

        EvidenceType.screenshot

        if evidence_type
        == "screenshot"

        else EvidenceType.file
    )


    # ========================================================
    # MIME
    # ========================================================

    mime_type = (
        file.content_type
        or ""
    ).lower()


    if (
        mime_type
        not in ALLOWED_MIME_TYPES
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=(
                "Type de fichier "
                "non autorisé."
            ),
        )


    if (
        evidence_enum
        == EvidenceType.screenshot

        and not mime_type.startswith(
            "image/"
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=(
                "Une capture d'écran "
                "doit être une image."
            ),
        )


    # ========================================================
    # FILE NAMES
    # ========================================================

    original_filename = (
        _safe_original_filename(
            file.filename
        )
    )


    extension = (
        _safe_extension(
            original_filename
        )
    )


    stored_filename = (

        f"{uuid.uuid4().hex}"
        f"{extension}"
    )


    case_directory = (

        PROTECTED_EVIDENCE_ROOT
        / str(case.id)
    )


    case_directory.mkdir(
        parents=True,
        exist_ok=True,
    )


    storage_path = (

        case_directory
        / stored_filename
    )


    # ========================================================
    # STREAM + HASH + SIZE
    # ========================================================

    sha256_hasher = (
        hashlib.sha256()
    )


    file_size = 0


    try:

        with storage_path.open(
            "wb"
        ) as destination:


            while True:

                chunk = (
                    await file.read(
                        CHUNK_SIZE
                    )
                )


                if not chunk:

                    break


                file_size += len(
                    chunk
                )


                if (
                    file_size
                    > MAX_FILE_SIZE
                ):

                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail=(
                            "Le fichier dépasse "
                            "la taille maximale "
                            "autorisée de 20 Mo."
                        ),
                    )


                sha256_hasher.update(
                    chunk
                )


                destination.write(
                    chunk
                )


    except Exception:

        if (
            storage_path.exists()
        ):

            storage_path.unlink(
                missing_ok=True
            )


        raise


    finally:

        await file.close()


    # ========================================================
    # EMPTY FILE
    # ========================================================

    if (
        file_size == 0
    ):

        storage_path.unlink(
            missing_ok=True
        )


        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Le fichier est vide."
            ),
        )


    sha256_value = (
        sha256_hasher.hexdigest()
    )


    # ========================================================
    # DATABASE OBJECT
    # ========================================================

    evidence = Evidence(

        case_id=case.id,

        type=evidence_enum,

        title=clean_title,

        original_filename=(
            original_filename
        ),

        stored_filename=(
            stored_filename
        ),

        storage_path=str(
            storage_path.resolve()
        ),

        mime_type=(
            mime_type
        ),

        file_size=(
            file_size
        ),

        sha256=(
            sha256_value
        ),

        url=None,

        note=None,
    )


    # ========================================================
    # SAVE EVIDENCE + HISTORY
    # ========================================================

    try:

        db.add(
            evidence
        )


        # Génère evidence.id.
        db.flush()


        _add_history_event(

            db=db,

            case_id=(
                case.id
            ),

            actor_user_id=(
                current_user.id
            ),

            event_type=(
                "evidence_added"
            ),

            event_data={

                "evidence_id":
                    str(evidence.id),

                "evidence_type":
                    evidence.type.value,

                "title":
                    evidence.title,

                "original_filename":
                    evidence.original_filename,

                "mime_type":
                    evidence.mime_type,

                "file_size":
                    evidence.file_size,
            },
        )


        db.commit()


        db.refresh(
            evidence
        )


    except Exception:

        db.rollback()


        storage_path.unlink(
            missing_ok=True
        )


        raise


    return evidence


# ============================================================
# LINK
# ============================================================

@router.post(
    "/cases/{case_id}/evidence/link",
    response_model=EvidencePublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def create_evidence_link(

    case_id: uuid.UUID,

    payload: EvidenceLinkCreate,

    current_user: User = Depends(
        get_current_user
    ),

    _csrf_checked: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),

) -> Evidence:

    _require_victim(
        current_user
    )


    case = _get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )


    evidence = Evidence(

        case_id=case.id,

        type=EvidenceType.link,

        title=(
            payload.title.strip()
        ),

        url=str(
            payload.url
        ),

        original_filename=None,

        stored_filename=None,

        storage_path=None,

        mime_type=None,

        file_size=None,

        sha256=None,

        note=None,
    )


    try:

        db.add(
            evidence
        )


        db.flush()


        _add_history_event(

            db=db,

            case_id=(
                case.id
            ),

            actor_user_id=(
                current_user.id
            ),

            event_type=(
                "evidence_added"
            ),

            event_data={

                "evidence_id":
                    str(evidence.id),

                "evidence_type":
                    evidence.type.value,

                "title":
                    evidence.title,
            },
        )


        db.commit()


        db.refresh(
            evidence
        )


    except Exception:

        db.rollback()

        raise


    return evidence


# ============================================================
# NOTE
# ============================================================

@router.post(
    "/cases/{case_id}/evidence/note",
    response_model=EvidencePublic,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def create_evidence_note(

    case_id: uuid.UUID,

    payload: EvidenceNoteCreate,

    current_user: User = Depends(
        get_current_user
    ),

    _csrf_checked: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),

) -> Evidence:

    _require_victim(
        current_user
    )


    case = _get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )


    evidence = Evidence(

        case_id=case.id,

        type=EvidenceType.note,

        title=(
            payload.title.strip()
        ),

        note=(
            payload.note.strip()
        ),

        original_filename=None,

        stored_filename=None,

        storage_path=None,

        mime_type=None,

        file_size=None,

        sha256=None,

        url=None,
    )


    try:

        db.add(
            evidence
        )


        db.flush()


        _add_history_event(

            db=db,

            case_id=(
                case.id
            ),

            actor_user_id=(
                current_user.id
            ),

            event_type=(
                "evidence_added"
            ),

            event_data={

                "evidence_id":
                    str(evidence.id),

                "evidence_type":
                    evidence.type.value,

                "title":
                    evidence.title,
            },
        )


        db.commit()


        db.refresh(
            evidence
        )


    except Exception:

        db.rollback()

        raise


    return evidence


# ============================================================
# LIST
# ============================================================

@router.get(
    "/cases/{case_id}/evidence",

    response_model=list[
        EvidencePublic
    ],
)
def list_case_evidence(

    case_id: uuid.UUID,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

) -> list[Evidence]:

    _require_victim(
        current_user
    )


    case = _get_owned_case(
        case_id=case_id,
        current_user=current_user,
        db=db,
    )


    evidences = (

        db.query(
            Evidence
        )

        .filter(
            Evidence.case_id
            == case.id
        )

        .order_by(
            Evidence.created_at.desc()
        )

        .all()
    )


    return evidences


# ============================================================
# DOWNLOAD
# ============================================================

@router.get(
    "/evidence/{evidence_id}/download"
)
def download_evidence(

    evidence_id: uuid.UUID,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    _require_victim(
        current_user
    )


    evidence = (
        _get_owned_evidence(

            evidence_id=(
                evidence_id
            ),

            current_user=(
                current_user
            ),

            db=db,
        )
    )


    if (
        evidence.type
        not in {
            EvidenceType.file,
            EvidenceType.screenshot,
        }
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Cette preuve "
                "ne contient pas de fichier."
            ),
        )


    if (
        not evidence.storage_path
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Fichier introuvable."
            ),
        )


    storage_path = Path(
        evidence.storage_path
    )


    if (
        not storage_path.exists()

        or not storage_path.is_file()
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Fichier introuvable."
            ),
        )


    return FileResponse(

        path=str(
            storage_path
        ),

        media_type=(
            evidence.mime_type
            or "application/octet-stream"
        ),

        filename=(
            evidence.original_filename
            or "preuve"
        ),
    )


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/evidence/{evidence_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
def delete_evidence(

    evidence_id: uuid.UUID,

    current_user: User = Depends(
        get_current_user
    ),

    _csrf_checked: None = Depends(
        verify_csrf
    ),

    db: Session = Depends(
        get_db
    ),

) -> Response:

    _require_victim(
        current_user
    )


    evidence = (
        _get_owned_evidence(

            evidence_id=(
                evidence_id
            ),

            current_user=(
                current_user
            ),

            db=db,
        )
    )


    # ========================================================
    # SAVE INFORMATION BEFORE DELETE
    # ========================================================

    case_id = (
        evidence.case_id
    )


    deleted_event_data = {

        "evidence_id":
            str(evidence.id),

        "evidence_type":
            evidence.type.value,

        "title":
            evidence.title,

        "original_filename":
            evidence.original_filename,
    }


    storage_path = None


    if (
        evidence.storage_path
    ):

        storage_path = Path(
            evidence.storage_path
        )


    # ========================================================
    # DATABASE DELETE + HISTORY
    # ========================================================

    try:

        _add_history_event(

            db=db,

            case_id=(
                case_id
            ),

            actor_user_id=(
                current_user.id
            ),

            event_type=(
                "evidence_deleted"
            ),

            event_data=(
                deleted_event_data
            ),
        )


        db.delete(
            evidence
        )


        db.commit()


    except Exception:

        db.rollback()

        raise


    # ========================================================
    # PHYSICAL FILE DELETE
    # ========================================================

    if (
        storage_path is not None

        and storage_path.exists()
    ):

        storage_path.unlink(
            missing_ok=True
        )


    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )