"""
api/routers/admin_cases.py

Gestion administrative des dossiers EMC Helpline.

Sécurité :
- toutes les routes sont réservées au rôle admin ;
- la liste expose uniquement les métadonnées nécessaires ;
- la description sensible n'est retournée que lors de l'ouverture
  explicite d'un dossier ;
- la liste expose une identité administrative limitée (nom, ID EMC,
  téléphone et CIN masquée) ;
- l'e-mail et la CIN complète ne sont retournés qu'après ouverture
  explicite du dossier par un administrateur ;
- la liste du dossier expose seulement les métadonnées des preuves ;
- le contenu d'une preuve n'est retourné qu'après consultation explicite ;
- les fichiers restent dans le stockage protégé ;
- toute modification de statut est protégée par CSRF ;
- chaque changement de statut est journalisé dans HistoryEvent.
"""

import hashlib
import html
import io
import os
import re
import tempfile
import uuid

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from fastapi.responses import FileResponse

from starlette.background import BackgroundTask

from pypdf import (
    PdfReader,
    PdfWriter,
)

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_LEFT,
    TA_RIGHT,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from sqlalchemy import (
    func,
    or_,
    select,
)

from sqlalchemy.orm import (
    Session,
    joinedload,
    selectinload,
)

from api.deps import (
    require_role,
    verify_csrf,
)

from auth.pii_crypto import (
    decrypt_sensitive,
)

from db.admin_cases_schemas import (
    AdminCaseDetail,
    AdminCaseListItem,
    AdminCasesPublic,
    AdminCasesSummary,
    AdminCaseStatusUpdate,
    AdminCaseWorkflowStatusUpdate,
    AdminEvidenceDetail,
    AdminEvidenceListItem,
    AdminDeletionRequestDecision,
    AdminDeletionRequestResult,
)

from db.database import get_db

from db.victim_profile_model import (
    VictimProfile,
)

from db.models import (
    ActionPlan,
    Case,
    CaseStatus,
    CaseWorkflowStatus,
    Evidence,
    EvidenceType,
    HistoryEvent,
    User,
    UserRole,
)


router = APIRouter(
    tags=["admin-cases"],
)


def _status_value(
    value,
) -> str:
    if hasattr(
        value,
        "value",
    ):
        return str(
            value.value
        )

    return str(value)


def _build_emc_id(
    user_id,
) -> str:
    if not user_id:
        return "—"

    compact = (
        str(user_id)
        .replace("-", "")
        .upper()
    )

    return f"V-{compact[:12]}"


def _mask_cin(
    cin: str | None,
) -> str | None:
    if not cin:
        return None

    clean = (
        str(cin)
        .strip()
        .upper()
    )

    if len(clean) <= 4:
        return "•" * len(clean)

    prefix_length = min(
        2,
        max(
            1,
            len(clean) - 4,
        ),
    )

    hidden_length = max(
        2,
        len(clean)
        - prefix_length
        - 2,
    )

    return (
        clean[:prefix_length]
        + ("•" * hidden_length)
        + clean[-2:]
    )


def _safe_decrypt_cin(
    profile: VictimProfile | None,
) -> str | None:
    if (
        profile is None
        or not profile.cin_encrypted
    ):
        return None

    try:
        return decrypt_sensitive(
            profile.cin_encrypted
        )
    except Exception:
        return None


def _identity_complete(
    profile: VictimProfile | None,
) -> bool:
    if profile is None:
        return False

    return all(
        [
            profile.first_name,
            profile.last_name,
            profile.date_of_birth,
            profile.phone,
            profile.cin_encrypted,
        ]
    )


def _victim_identity(
    case: Case,
    db: Session,
) -> dict:
    user = case.user

    if user is None:
        return {
            "username": "—",
            "full_name": None,
            "emc_id": "—",
            "phone": None,
            "cin": None,
            "cin_masked": None,
            "email": None,
            "date_of_birth": None,
            "identity_complete": False,
        }

    profile = db.get(
        VictimProfile,
        user.id,
    )

    cin = _safe_decrypt_cin(
        profile
    )

    full_name = None

    if profile is not None:
        full_name = (
            " ".join(
                value
                for value in [
                    profile.first_name,
                    profile.last_name,
                ]
                if value
            ).strip()
            or None
        )

    return {
        "username": user.username,
        "full_name": full_name,
        "emc_id": _build_emc_id(user.id),
        "phone": (
            profile.phone
            if profile
            else None
        ),
        "cin": cin,
        "cin_masked": _mask_cin(cin),
        "email": user.email,
        "date_of_birth": (
            profile.date_of_birth
            if profile
            else None
        ),
        "identity_complete": _identity_complete(
            profile
        ),
    }


def _workflow_status_value(
    value,
) -> str:
    if hasattr(
        value,
        "value",
    ):
        return str(
            value.value
        )

    return str(value)


def _evidence_type_value(
    value,
) -> str:
    if hasattr(
        value,
        "value",
    ):
        return str(
            value.value
        )

    return str(value)


def _to_evidence_list_item(
    evidence: Evidence,
) -> AdminEvidenceListItem:
    return AdminEvidenceListItem(
        id=evidence.id,
        type=_evidence_type_value(
            evidence.type
        ),
        title=evidence.title,
        original_filename=(
            evidence.original_filename
        ),
        mime_type=(
            evidence.mime_type
        ),
        file_size=(
            evidence.file_size
        ),
        created_at=(
            evidence.created_at
        ),
    )


def _to_evidence_detail(
    evidence: Evidence,
) -> AdminEvidenceDetail:
    item = _to_evidence_list_item(
        evidence
    )

    evidence_type = (
        _evidence_type_value(
            evidence.type
        )
    )

    return AdminEvidenceDetail(
        **item.model_dump(),
        url=evidence.url,
        note=evidence.note,
        has_download=(
            evidence_type
            in {
                "file",
                "screenshot",
            }
            and bool(
                evidence.storage_path
            )
        ),
    )


def _deletion_request_state(
    *,
    case_id: uuid.UUID,
    db: Session,
) -> tuple[bool, str]:
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

    if event_type == "case_deletion_requested":
        return (True, "pending")

    if event_type == "case_deletion_rejected":
        return (False, "rejected")

    return (False, "none")


def _to_list_item(
    case: Case,
    db: Session,
) -> AdminCaseListItem:
    evidences = (
        case.evidences
        or []
    )

    plan = case.action_plan

    actions = (
        plan.items
        if plan is not None
        else []
    )

    total_actions = len(
        actions
    )

    completed_actions = sum(
        1
        for item
        in actions
        if item.completed
    )

    action_progress = (
        round(
            (
                completed_actions
                / total_actions
            )
            * 100,
            1,
        )
        if total_actions > 0
        else 0.0
    )

    identity = _victim_identity(
        case,
        db,
    )

    (
        deletion_requested,
        deletion_request_status,
    ) = _deletion_request_state(
        case_id=case.id,
        db=db,
    )

    return AdminCaseListItem(
        id=case.id,

        victim_username=(
            identity["username"]
        ),

        victim_full_name=(
            identity["full_name"]
        ),

        victim_emc_id=(
            identity["emc_id"]
        ),

        victim_phone=(
            identity["phone"]
        ),

        victim_cin_masked=(
            identity["cin_masked"]
        ),

        victim_identity_complete=(
            identity["identity_complete"]
        ),

        deletion_requested=(
            deletion_requested
        ),

        deletion_request_status=(
            deletion_request_status
        ),

        detected_intent=(
            case.detected_intent
        ),

        language=(
            case.language
        ),

        status=_status_value(
            case.status
        ),

        workflow_status=(
            _workflow_status_value(
                case.workflow_status
            )
        ),

        emergency=bool(
            case.emergency
        ),

        evidence_count=len(
            evidences
        ),

        has_action_plan=(
            plan is not None
        ),

        total_actions=(
            total_actions
        ),

        completed_actions=(
            completed_actions
        ),

        action_progress=(
            action_progress
        ),

        created_at=(
            case.created_at
        ),

        updated_at=(
            case.updated_at
        ),
    )


def _to_detail(
    case: Case,
    db: Session,
) -> AdminCaseDetail:
    item = _to_list_item(
        case,
        db,
    )

    identity = _victim_identity(
        case,
        db,
    )

    return AdminCaseDetail(
        **item.model_dump(),

        victim_email=(
            identity["email"]
        ),

        victim_cin=(
            identity["cin"]
        ),

        victim_date_of_birth=(
            identity["date_of_birth"]
        ),

        description=case.description,
        evidences=[
            _to_evidence_list_item(
                evidence
            )
            for evidence
            in (
                case.evidences
                or []
            )
        ],
    )


def _base_case_query():
    return (
        select(Case)
        .join(
            User,
            User.id
            == Case.user_id,
        )
        .options(
            joinedload(
                Case.user
            ),
            selectinload(
                Case.evidences
            ),
            selectinload(
                Case.action_plan
            ).selectinload(
                ActionPlan.items
            ),
            selectinload(
                Case.history_events
            ),
        )
    )


def _load_admin_case(
    case_id: uuid.UUID,
    db: Session,
) -> Case:
    statement = (
        _base_case_query()
        .where(
            Case.id
            == case_id
        )
    )

    case = db.scalar(
        statement
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


def _load_admin_evidence(
    *,
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: Session,
) -> Evidence:
    evidence = db.scalar(
        select(
            Evidence
        )
        .where(
            Evidence.id
            == evidence_id,
            Evidence.case_id
            == case_id,
        )
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



# ============================================================
# EXPORT PDF COMPLET DU DOSSIER
# ============================================================

_INVALID_FILENAME = re.compile(
    r'[<>:"/\\|?*\x00-\x1f]+'
)


def _safe_filename(
    value: str | None,
    fallback: str,
) -> str:
    clean = (
        (value or "")
        .strip()
    )

    clean = _INVALID_FILENAME.sub(
        "_",
        clean,
    )

    clean = re.sub(
        r"\s+",
        " ",
        clean,
    ).strip(
        " ."
    )

    if not clean:
        clean = fallback

    return clean[:140]


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda:
                handle.read(
                    1024 * 1024
                ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def _pdf_font_names():
    """
    Utilise une police Unicode disponible localement pour FR / AR.
    """

    candidates = [
        (
            "EMCRegular",
            "EMCBold",
            Path(
                "C:/Windows/Fonts/arial.ttf"
            ),
            Path(
                "C:/Windows/Fonts/arialbd.ttf"
            ),
        ),
        (
            "EMCRegular",
            "EMCBold",
            Path(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            ),
            Path(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            ),
        ),
    ]

    for (
        regular_name,
        bold_name,
        regular_path,
        bold_path,
    ) in candidates:
        if (
            regular_path.exists()
            and bold_path.exists()
        ):
            if (
                regular_name
                not in pdfmetrics
                .getRegisteredFontNames()
            ):
                pdfmetrics.registerFont(
                    TTFont(
                        regular_name,
                        str(
                            regular_path
                        ),
                    )
                )

            if (
                bold_name
                not in pdfmetrics
                .getRegisteredFontNames()
            ):
                pdfmetrics.registerFont(
                    TTFont(
                        bold_name,
                        str(
                            bold_path
                        ),
                    )
                )

            return (
                regular_name,
                bold_name,
            )

    return (
        "Helvetica",
        "Helvetica-Bold",
    )


def _pdf_display_text(
    value: str | None,
    *,
    rtl: bool,
) -> str:
    text = (
        value
        or "—"
    )

    if rtl:
        try:
            import arabic_reshaper
            from bidi.algorithm import (
                get_display,
            )

            text = get_display(
                arabic_reshaper.reshape(
                    text
                )
            )
        except ImportError:
            # Le rapport reste générable.
            # Pour un rendu arabe correct :
            # pip install arabic-reshaper python-bidi
            pass

    return html.escape(
        text
    ).replace(
        "\n",
        "<br/>",
    )


def _format_export_date(
    value,
) -> str:
    if not value:
        return "—"

    try:
        return value.astimezone(
            timezone.utc
        ).strftime(
            "%d/%m/%Y %H:%M UTC"
        )
    except Exception:
        return str(value)


def _evidence_integrity(
    evidence: Evidence,
    storage_path: Path | None,
) -> tuple[
    str | None,
    str,
]:
    """
    Retourne :
    (sha256 recalculé, état d'intégrité)
    """

    if (
        storage_path is None
        or not storage_path.exists()
        or not storage_path.is_file()
    ):
        if evidence.storage_path:
            return (
                None,
                "missing",
            )

        return (
            None,
            "not_applicable",
        )

    calculated = (
        _sha256_file(
            storage_path
        )
    )

    if not evidence.sha256:
        return (
            calculated,
            "hash_not_recorded",
        )

    if (
        evidence.sha256.lower()
        == calculated.lower()
    ):
        return (
            calculated,
            "verified",
        )

    return (
        calculated,
        "mismatch",
    )


def _integrity_label(
    value: str,
    *,
    rtl: bool,
) -> str:
    labels_fr = {
        "verified":
            "Intégrité vérifiée",
        "mismatch":
            "Empreinte différente",
        "hash_not_recorded":
            "Empreinte non enregistrée",
        "missing":
            "Fichier introuvable",
        "not_applicable":
            "Non applicable",
    }

    labels_ar = {
        "verified":
            "تم التحقق من السلامة",
        "mismatch":
            "البصمة مختلفة",
        "hash_not_recorded":
            "البصمة غير مسجلة",
        "missing":
            "الملف غير موجود",
        "not_applicable":
            "غير مطبق",
    }

    return (
        labels_ar
        if rtl
        else labels_fr
    ).get(
        value,
        value,
    )


def _prepare_evidence_entries(
    case: Case,
) -> list[dict]:
    entries = []

    for index, evidence in enumerate(
        case.evidences
        or [],
        start=1,
    ):
        evidence_type = (
            _evidence_type_value(
                evidence.type
            )
        )

        storage_path = (
            Path(
                evidence.storage_path
            )
            if evidence.storage_path
            else None
        )

        suffix = (
            storage_path.suffix.lower()
            if storage_path
            else ""
        )

        mime_type = (
            evidence.mime_type
            or ""
        ).lower()

        is_image = (
            evidence_type
            == "screenshot"
            or mime_type.startswith(
                "image/"
            )
            or suffix
            in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".bmp",
                ".gif",
            }
        )

        is_pdf = (
            mime_type
            == "application/pdf"
            or suffix == ".pdf"
        )

        is_text_file = (
            mime_type.startswith(
                "text/"
            )
            or suffix
            in {
                ".txt",
                ".md",
                ".csv",
                ".log",
                ".json",
            }
        )

        (
            calculated_hash,
            integrity_status,
        ) = _evidence_integrity(
            evidence,
            storage_path,
        )

        pdf_page_count = None
        pdf_appendable = False

        if (
            is_pdf
            and storage_path
            and storage_path.exists()
            and storage_path.is_file()
        ):
            try:
                pdf_reader = PdfReader(
                    str(
                        storage_path
                    )
                )

                if (
                    pdf_reader.is_encrypted
                ):
                    try:
                        pdf_reader.decrypt(
                            ""
                        )
                    except Exception:
                        pass

                pdf_page_count = len(
                    pdf_reader.pages
                )

                pdf_appendable = (
                    pdf_page_count > 0
                )
            except Exception:
                pdf_appendable = False

        entries.append(
            {
                "index":
                    index,
                "id":
                    str(
                        evidence.id
                    ),
                "type":
                    evidence_type,
                "title":
                    evidence.title,
                "created_at":
                    evidence.created_at,
                "url":
                    evidence.url,
                "note":
                    evidence.note,
                "original_filename":
                    evidence.original_filename,
                "mime_type":
                    evidence.mime_type,
                "file_size":
                    evidence.file_size,
                "storage_path":
                    storage_path,
                "is_image":
                    is_image,
                "is_pdf":
                    is_pdf,
                "is_text_file":
                    is_text_file,
                "pdf_appendable":
                    pdf_appendable,
                "pdf_page_count":
                    pdf_page_count,
                "sha256_recorded":
                    evidence.sha256,
                "sha256_calculated":
                    calculated_hash,
                "integrity_status":
                    integrity_status,
            }
        )

    return entries


def _read_text_evidence(
    path: Path,
    *,
    max_characters: int = 20000,
) -> str:
    try:
        raw = path.read_bytes()

        for encoding in (
            "utf-8",
            "utf-8-sig",
            "latin-1",
        ):
            try:
                return (
                    raw.decode(
                        encoding
                    )
                    [:max_characters]
                )
            except UnicodeDecodeError:
                continue
    except Exception:
        pass

    return ""


def _scaled_reportlab_image(
    path: Path,
    *,
    max_width: float,
    max_height: float,
):
    reader = ImageReader(
        str(
            path
        )
    )

    width, height = (
        reader.getSize()
    )

    if (
        width <= 0
        or height <= 0
    ):
        raise ValueError(
            "Dimensions d'image invalides."
        )

    ratio = min(
        max_width / width,
        max_height / height,
        1.0,
    )

    return RLImage(
        str(
            path
        ),
        width=(
            width * ratio
        ),
        height=(
            height * ratio
        ),
    )



def _platform_gradient(
    canvas,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
):
    """Dégradé EMC Helpline : orange -> rose -> violet."""
    stops = [
        (0.0, (0.969, 0.627, 0.235)),
        (0.38, (0.957, 0.424, 0.459)),
        (0.68, (0.851, 0.329, 0.604)),
        (1.0, (0.439, 0.282, 0.722)),
    ]

    steps = 80

    for index in range(steps):
        t = index / max(steps - 1, 1)

        left = stops[0]
        right = stops[-1]

        for stop_index in range(len(stops) - 1):
            current = stops[stop_index]
            nxt = stops[stop_index + 1]

            if current[0] <= t <= nxt[0]:
                left = current
                right = nxt
                break

        span = max(
            right[0] - left[0],
            0.0001,
        )

        local_t = (
            t - left[0]
        ) / span

        color = tuple(
            left[1][channel]
            + (
                right[1][channel]
                - left[1][channel]
            )
            * local_t
            for channel in range(3)
        )

        canvas.setFillColorRGB(
            *color
        )

        canvas.rect(
            x
            + width
            * index
            / steps,
            y,
            width / steps + 0.8,
            height,
            stroke=0,
            fill=1,
        )


def _platform_pdf_page_callback(
    *,
    case_reference: str,
    regular_font: str,
    bold_font: str,
):
    """Habillage de page cohérent avec l'interface EMC Helpline."""

    def draw_page(
        canvas,
        doc,
    ):
        page_width, page_height = A4

        canvas.saveState()

        # Fond général clair de la plateforme.
        canvas.setFillColor(
            colors.HexColor(
                "#F8F7FC"
            )
        )

        canvas.rect(
            0,
            0,
            page_width,
            page_height,
            stroke=0,
            fill=1,
        )

        # Header violet, proche de la sidebar.
        header_height = (
            23 * mm
        )

        canvas.setFillColor(
            colors.HexColor(
                "#321A67"
            )
        )

        canvas.rect(
            0,
            page_height
            - header_height,
            page_width,
            header_height,
            stroke=0,
            fill=1,
        )

        _platform_gradient(
            canvas,
            x=0,
            y=(
                page_height
                - header_height
            ),
            width=page_width,
            height=2.4 * mm,
        )

        # Badge EMC.
        badge_size = (
            10.5 * mm
        )

        badge_x = (
            16 * mm
        )

        badge_y = (
            page_height
            - header_height
            + 6.2 * mm
        )

        canvas.setFillColor(
            colors.white
        )

        canvas.roundRect(
            badge_x,
            badge_y,
            badge_size,
            badge_size,
            2.7 * mm,
            stroke=0,
            fill=1,
        )

        canvas.setFillColor(
            colors.HexColor(
                "#7048B8"
            )
        )

        canvas.setFont(
            bold_font,
            8.1,
        )

        canvas.drawCentredString(
            badge_x
            + badge_size / 2,
            badge_y
            + 4.0 * mm,
            "EMC",
        )

        # Point vert de sécurité / disponibilité.
        canvas.setFillColor(
            colors.HexColor(
                "#45C992"
            )
        )

        canvas.circle(
            badge_x
            + badge_size
            - 0.7 * mm,
            badge_y
            + 1.0 * mm,
            1.05 * mm,
            stroke=0,
            fill=1,
        )

        canvas.setFillColor(
            colors.white
        )

        canvas.setFont(
            bold_font,
            10.8,
        )

        canvas.drawString(
            badge_x
            + badge_size
            + 4 * mm,
            badge_y
            + 5.8 * mm,
            "EMC Helpline",
        )

        canvas.setFillColor(
            colors.HexColor(
                "#D9D0E8"
            )
        )

        canvas.setFont(
            regular_font,
            7.2,
        )

        canvas.drawString(
            badge_x
            + badge_size
            + 4 * mm,
            badge_y
            + 2.1 * mm,
            "Rapport administratif sécurisé",
        )

        canvas.setFillColor(
            colors.white
        )

        canvas.setFont(
            bold_font,
            8.5,
        )

        canvas.drawRightString(
            page_width
            - 16 * mm,
            badge_y
            + 4.8 * mm,
            f"Dossier {case_reference}",
        )

        # Footer de plateforme.
        footer_y = (
            10.3 * mm
        )

        _platform_gradient(
            canvas,
            x=16 * mm,
            y=footer_y
            + 5.0 * mm,
            width=page_width
            - 32 * mm,
            height=0.75 * mm,
        )

        canvas.setFillColor(
            colors.HexColor(
                "#8D8596"
            )
        )

        canvas.setFont(
            regular_font,
            7.0,
        )

        canvas.drawString(
            16 * mm,
            footer_y,
            "EMC Helpline - espace d'administration sécurisé",
        )

        canvas.drawRightString(
            page_width
            - 16 * mm,
            footer_y,
            f"Page {doc.page}",
        )

        canvas.restoreState()

    return draw_page


def _build_case_report_pdf(
    *,
    case: Case,
    victim_identity: dict,
    generated_by: str,
    generated_at: datetime,
    evidence_entries: list[dict],
) -> bytes:
    buffer = io.BytesIO()

    (
        regular_font,
        bold_font,
    ) = _pdf_font_names()

    is_rtl = (
        case.language
        == "ar"
    )

    align = (
        TA_RIGHT
        if is_rtl
        else TA_LEFT
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "EMCTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=21,
        leading=26,
        textColor=colors.HexColor(
            "#241D46"
        ),
        alignment=align,
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "EMCSubtitle",
        parent=styles["Heading2"],
        fontName=regular_font,
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor(
            "#7C7486"
        ),
        alignment=align,
        spaceAfter=10,
    )

    heading_style = ParagraphStyle(
        "EMCHeading",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor(
            "#2B185D"
        ),
        backColor=colors.HexColor(
            "#F4EFFC"
        ),
        borderColor=colors.HexColor(
            "#E2D8EA"
        ),
        borderWidth=0.45,
        borderPadding=7,
        alignment=align,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "EMCBody",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=9.8,
        leading=14.5,
        textColor=colors.HexColor(
            "#514A5B"
        ),
        alignment=align,
    )

    small_style = ParagraphStyle(
        "EMCSmall",
        parent=body_style,
        fontSize=8.2,
        leading=11.5,
        textColor=colors.HexColor(
            "#77707E"
        ),
    )

    proof_title_style = ParagraphStyle(
        "EMCProofTitle",
        parent=body_style,
        fontName=bold_font,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor(
            "#2B185D"
        ),
    )

    link_style = ParagraphStyle(
        "EMCLink",
        parent=body_style,
        fontSize=9.2,
        leading=14,
        textColor=colors.HexColor(
            "#7048B8"
        ),
    )

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=31 * mm,
        bottomMargin=23 * mm,
        title=(
            f"Dossier EMC "
            f"{str(case.id)[:8].upper()}"
        ),
        author="EMC Helpline",
    )

    story = []

    # ========================================================
    # EN-TÊTE
    # ========================================================

    reference = (
        f"#{str(case.id)[:8].upper()}"
    )

    hero_copy = [
        Paragraph(
            _pdf_display_text(
                (
                    "Rapport complet du dossier"
                    if not is_rtl
                    else "التقرير الكامل للملف"
                ),
                rtl=is_rtl,
            ),
            title_style,
        ),
        Paragraph(
            _pdf_display_text(
                (
                    "Situation, suivi, plan d'action et preuves"
                    if not is_rtl
                    else "الحالة والمتابعة وخطة العمل والأدلة"
                ),
                rtl=is_rtl,
            ),
            subtitle_style,
        ),
    ]

    hero_ref = Table(
        [
            [
                Paragraph(
                    _pdf_display_text(
                        (
                            "DOSSIER"
                            if not is_rtl
                            else "الملف"
                        ),
                        rtl=is_rtl,
                    ),
                    small_style,
                )
            ],
            [
                Paragraph(
                    reference,
                    proof_title_style,
                )
            ],
        ],
        colWidths=[
            34 * mm,
        ],
    )

    hero_ref.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F1EBFB"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    colors.HexColor(
                        "#DCCFE7"
                    ),
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    hero_table = Table(
        [
            [
                hero_copy,
                hero_ref,
            ]
        ],
        colWidths=[
            134 * mm,
            34 * mm,
        ],
    )

    hero_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.55,
                    colors.HexColor(
                        "#E4DCE9"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    11,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    11,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "LEFTPADDING",
                    (1, 0),
                    (1, 0),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (1, 0),
                    (1, 0),
                    0,
                ),
            ]
        )
    )

    story.append(
        hero_table
    )

    story.append(
        Spacer(
            1,
            8,
        )
    )

    # ========================================================
    # CARTES D'INFORMATIONS - même logique que le dashboard
    # ========================================================

    metadata_items = [
        (
            "Victime"
            if not is_rtl
            else "الضحية",
            (
                victim_identity.get("full_name")
                or victim_identity.get("username")
                or "—"
            ),
            "#F4EFFC",
        ),
        (
            "Situation détectée"
            if not is_rtl
            else "الحالة المكتشفة",
            (
                case.detected_intent
                or "—"
            ),
            "#EFF5FE",
        ),
        (
            "Statut"
            if not is_rtl
            else "الحالة",
            (
                "Actif"
                if _status_value(case.status) == "active"
                else "Clôturé"
            )
            if not is_rtl
            else (
                "نشط"
                if _status_value(case.status) == "active"
                else "مغلق"
            ),
            "#EEF9F5",
        ),
        (
            "Prise en charge"
            if not is_rtl
            else "مرحلة المعالجة",
            {
                "new": (
                    "Nouveau"
                    if not is_rtl
                    else "جديد"
                ),
                "in_progress": (
                    "En cours de traitement"
                    if not is_rtl
                    else "قيد المعالجة"
                ),
                "waiting_information": (
                    "En attente d'informations"
                    if not is_rtl
                    else "في انتظار معلومات"
                ),
                "resolved": (
                    "Résolu"
                    if not is_rtl
                    else "تمت المعالجة"
                ),
                "closed": (
                    "Clôturé"
                    if not is_rtl
                    else "مغلق"
                ),
            }.get(
                _workflow_status_value(
                    case.workflow_status
                ),
                _workflow_status_value(
                    case.workflow_status
                ),
            ),
            "#F4EFFC",
        ),
        (
            "Langue"
            if not is_rtl
            else "اللغة",
            (
                (case.language or "—")
                .upper()
            ),
            "#FFF5E9",
        ),
        (
            "Urgence"
            if not is_rtl
            else "طارئ",
            (
                "Oui"
                if case.emergency
                else "Non"
            )
            if not is_rtl
            else (
                "نعم"
                if case.emergency
                else "لا"
            ),
            (
                "#FFF0F1"
                if case.emergency
                else "#EEF9F5"
            ),
        ),
        (
            "Créé le"
            if not is_rtl
            else "تاريخ الإنشاء",
            _format_export_date(
                case.created_at
            ),
            "#FAF8FC",
        ),
        (
            "Dernière mise à jour"
            if not is_rtl
            else "آخر تحديث",
            _format_export_date(
                case.updated_at
            ),
            "#FAF8FC",
        ),
        (
            "Référence"
            if not is_rtl
            else "المرجع",
            reference,
            "#FAF8FC",
        ),
    ]

    metadata_cards = []

    for (
        label,
        value,
        background,
    ) in metadata_items:
        card = Table(
            [
                [
                    Paragraph(
                        _pdf_display_text(
                            label,
                            rtl=is_rtl,
                        ),
                        small_style,
                    )
                ],
                [
                    Paragraph(
                        _pdf_display_text(
                            value,
                            rtl=is_rtl,
                        ),
                        proof_title_style,
                    )
                ],
            ],
            colWidths=[
                39 * mm,
            ],
        )

        card.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        colors.HexColor(
                            background
                        ),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.45,
                        colors.HexColor(
                            "#E6E0EA"
                        ),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ]
            )
        )

        metadata_cards.append(
            card
        )

    metadata_rows = []

    for index in range(
        0,
        len(metadata_cards),
        4,
    ):
        row = metadata_cards[
            index:
            index + 4
        ]

        while len(row) < 4:
            row.append("")

        metadata_rows.append(
            row
        )

    metadata_grid = Table(
        metadata_rows,
        colWidths=[
            42.5 * mm,
            42.5 * mm,
            42.5 * mm,
            42.5 * mm,
        ],
    )

    metadata_grid.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    story.append(
        metadata_grid
    )

    # ========================================================
    # IDENTITÉ DE LA VICTIME
    # ========================================================

    story.append(
        Paragraph(
            _pdf_display_text(
                (
                    "Identité de la victime"
                    if not is_rtl
                    else "هوية الضحية"
                ),
                rtl=is_rtl,
            ),
            heading_style,
        )
    )

    birth_date = victim_identity.get(
        "date_of_birth"
    )

    if birth_date:
        try:
            birth_date_text = birth_date.strftime(
                "%d/%m/%Y"
            )
        except Exception:
            birth_date_text = str(
                birth_date
            )
    else:
        birth_date_text = "—"

    identity_rows = [
        (
            "Nom complet"
            if not is_rtl
            else "الاسم الكامل",
            victim_identity.get("full_name")
            or "—",
        ),
        (
            "Identifiant EMC"
            if not is_rtl
            else "معرف EMC",
            victim_identity.get("emc_id")
            or "—",
        ),
        (
            "Nom d'utilisateur"
            if not is_rtl
            else "اسم المستخدم",
            victim_identity.get("username")
            or "—",
        ),
        (
            "CIN"
            if not is_rtl
            else "رقم البطاقة الوطنية",
            victim_identity.get("cin")
            or "—",
        ),
        (
            "Téléphone"
            if not is_rtl
            else "الهاتف",
            victim_identity.get("phone")
            or "—",
        ),
        (
            "E-mail"
            if not is_rtl
            else "البريد الإلكتروني",
            victim_identity.get("email")
            or "—",
        ),
        (
            "Date de naissance"
            if not is_rtl
            else "تاريخ الميلاد",
            birth_date_text,
        ),
        (
            "État de l'identité"
            if not is_rtl
            else "حالة الهوية",
            (
                (
                    "Identité renseignée"
                    if not is_rtl
                    else "الهوية مكتملة"
                )
                if victim_identity.get(
                    "identity_complete"
                )
                else (
                    "Identité incomplète"
                    if not is_rtl
                    else "الهوية غير مكتملة"
                )
            ),
        ),
    ]

    identity_table = Table(
        [
            [
                Paragraph(
                    _pdf_display_text(
                        label,
                        rtl=is_rtl,
                    ),
                    small_style,
                ),
                Paragraph(
                    _pdf_display_text(
                        str(value),
                        rtl=is_rtl,
                    ),
                    body_style,
                ),
            ]
            for label, value in identity_rows
        ],
        colWidths=[
            45 * mm,
            127 * mm,
        ],
    )

    identity_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor(
                        "#F4EFFC"
                    ),
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, -1),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    colors.HexColor(
                        "#E3DBE9"
                    ),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.HexColor(
                        "#EEE8F2"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        identity_table
    )

    # ========================================================
    # SITUATION
    # ========================================================

    story.append(
        Paragraph(
            _pdf_display_text(
                (
                    "Situation déclarée"
                    if not is_rtl
                    else "الحالة المصرح بها"
                ),
                rtl=is_rtl,
            ),
            heading_style,
        )
    )

    situation_card = Table(
        [
            [
                Paragraph(
                    _pdf_display_text(
                        case.description,
                        rtl=is_rtl,
                    ),
                    body_style,
                )
            ]
        ],
        colWidths=[
            172 * mm,
        ],
    )

    situation_card.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.45,
                    colors.HexColor(
                        "#E6E1EC"
                    ),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(
        situation_card
    )

    # ========================================================
    # PLAN D'ACTION
    # ========================================================

    story.append(
        Paragraph(
            _pdf_display_text(
                (
                    "Plan d'action"
                    if not is_rtl
                    else "خطة العمل"
                ),
                rtl=is_rtl,
            ),
            heading_style,
        )
    )

    plan = case.action_plan

    if plan is None:
        story.append(
            Paragraph(
                _pdf_display_text(
                    (
                        "Aucun plan d'action enregistré."
                        if not is_rtl
                        else "لا توجد خطة عمل مسجلة."
                    ),
                    rtl=is_rtl,
                ),
                body_style,
            )
        )
    else:
        for item in (
            plan.items
            or []
        ):
            status_label = (
                "Terminé"
                if item.completed
                else "À faire"
            )

            if is_rtl:
                status_label = (
                    "منجز"
                    if item.completed
                    else "قيد التنفيذ"
                )

            number_box = Table(
                [
                    [
                        Paragraph(
                            str(
                                item.position
                            ),
                            proof_title_style,
                        )
                    ]
                ],
                colWidths=[
                    10 * mm,
                ],
                rowHeights=[
                    10 * mm,
                ],
            )

            number_box.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor(
                                "#F1EBFB"
                            ),
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.4,
                            colors.HexColor(
                                "#DED3E7"
                            ),
                        ),
                        (
                            "ALIGN",
                            (0, 0),
                            (-1, -1),
                            "CENTER",
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                    ]
                )
            )

            text_block = [
                Paragraph(
                    _pdf_display_text(
                        item.title,
                        rtl=is_rtl,
                    ),
                    proof_title_style,
                ),
                Paragraph(
                    _pdf_display_text(
                        item.description,
                        rtl=is_rtl,
                    ),
                    small_style,
                ),
            ]

            status_box = Table(
                [
                    [
                        Paragraph(
                            _pdf_display_text(
                                status_label,
                                rtl=is_rtl,
                            ),
                            small_style,
                        )
                    ]
                ],
                colWidths=[
                    25 * mm,
                ],
            )

            status_box.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor(
                                "#EAF7F1"
                                if item.completed
                                else "#FFF5E9"
                            ),
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.35,
                            colors.HexColor(
                                "#D8EDE3"
                                if item.completed
                                else "#F4DFC2"
                            ),
                        ),
                        (
                            "ALIGN",
                            (0, 0),
                            (-1, -1),
                            "CENTER",
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                    ]
                )
            )

            action_card = Table(
                [
                    [
                        number_box,
                        text_block,
                        status_box,
                    ]
                ],
                colWidths=[
                    14 * mm,
                    130 * mm,
                    28 * mm,
                ],
            )

            action_card.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.white,
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.45,
                            colors.HexColor(
                                "#E6E0EA"
                            ),
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                    ]
                )
            )

            story.append(
                action_card
            )

            story.append(
                Spacer(
                    1,
                    4,
                )
            )

    # ========================================================
    # PREUVES - CONTENU DIRECTEMENT DANS LE PDF
    # ========================================================

    story.append(
        Paragraph(
            _pdf_display_text(
                (
                    f"Preuves et justificatifs "
                    f"({len(evidence_entries)})"
                    if not is_rtl
                    else (
                        f"الأدلة والمستندات "
                        f"({len(evidence_entries)})"
                    )
                ),
                rtl=is_rtl,
            ),
            heading_style,
        )
    )

    if not evidence_entries:
        story.append(
            Paragraph(
                _pdf_display_text(
                    (
                        "Aucune preuve enregistrée."
                        if not is_rtl
                        else "لا توجد أدلة مسجلة."
                    ),
                    rtl=is_rtl,
                ),
                body_style,
            )
        )

    for entry in evidence_entries:
        index = entry[
            "index"
        ]

        evidence_type = entry[
            "type"
        ]

        title = entry[
            "title"
        ]

        type_label_fr = {
            "screenshot":
                "Capture d'écran",
            "file":
                "Fichier",
            "link":
                "Lien",
            "note":
                "Note",
        }.get(
            evidence_type,
            evidence_type,
        )

        type_label_ar = {
            "screenshot":
                "لقطة شاشة",
            "file":
                "ملف",
            "link":
                "رابط",
            "note":
                "ملاحظة",
        }.get(
            evidence_type,
            evidence_type,
        )

        story.append(
            Spacer(
                1,
                6,
            )
        )

        proof_header = Table(
            [
                [
                    Paragraph(
                        _pdf_display_text(
                            (
                                f"Preuve {index} - {title}"
                                if not is_rtl
                                else (
                                    f"الدليل {index} - {title}"
                                )
                            ),
                            rtl=is_rtl,
                        ),
                        proof_title_style,
                    ),
                    Paragraph(
                        _pdf_display_text(
                            (
                                type_label_fr
                                if not is_rtl
                                else type_label_ar
                            ),
                            rtl=is_rtl,
                        ),
                        small_style,
                    ),
                ]
            ],
            colWidths=[
                135 * mm,
                37 * mm,
            ],
        )

        proof_header.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        colors.HexColor(
                            "#F5F0FC"
                        ),
                    ),
                    (
                        "BOX",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        0.5,
                        colors.HexColor(
                            "#DED4E8"
                        ),
                    ),
                    (
                        "VALIGN",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (
                            0,
                            0,
                        ),
                        (
                            -1,
                            -1,
                        ),
                        7,
                    ),
                ]
            )
        )

        story.append(
            proof_header
        )

        metadata_text = (
            f"Ajoutée le "
            f"{_format_export_date(entry['created_at'])}"
            if not is_rtl
            else (
                "أضيفت في "
                f"{_format_export_date(entry['created_at'])}"
            )
        )

        if entry[
            "original_filename"
        ]:
            metadata_text += (
                " - "
                + (
                    "Fichier : "
                    if not is_rtl
                    else "الملف: "
                )
                + entry[
                    "original_filename"
                ]
            )

        story.append(
            Paragraph(
                _pdf_display_text(
                    metadata_text,
                    rtl=is_rtl,
                ),
                small_style,
            )
        )

        # ----------------------------------------------------
        # CAPTURE / IMAGE : image directement dans le rapport
        # ----------------------------------------------------

        if (
            entry[
                "is_image"
            ]
            and entry[
                "storage_path"
            ]
            and entry[
                "storage_path"
            ].exists()
        ):
            try:
                image = (
                    _scaled_reportlab_image(
                        entry[
                            "storage_path"
                        ],
                        max_width=(
                            168 * mm
                        ),
                        max_height=(
                            115 * mm
                        ),
                    )
                )

                image_box = Table(
                    [
                        [
                            image
                        ]
                    ],
                    colWidths=[
                        172 * mm
                    ],
                )

                image_box.setStyle(
                    TableStyle(
                        [
                            (
                                "BOX",
                                (
                                    0,
                                    0,
                                ),
                                (
                                    -1,
                                    -1,
                                ),
                                0.5,
                                colors.HexColor(
                                    "#DDD6E3"
                                ),
                            ),
                            (
                                "BACKGROUND",
                                (
                                    0,
                                    0,
                                ),
                                (
                                    -1,
                                    -1,
                                ),
                                colors.white,
                            ),
                            (
                                "ALIGN",
                                (
                                    0,
                                    0,
                                ),
                                (
                                    -1,
                                    -1,
                                ),
                                "CENTER",
                            ),
                            (
                                "VALIGN",
                                (
                                    0,
                                    0,
                                ),
                                (
                                    -1,
                                    -1,
                                ),
                                "MIDDLE",
                            ),
                            (
                                "TOPPADDING",
                                (
                                    0,
                                    0,
                                ),
                                (
                                    -1,
                                    -1,
                                ),
                                7,
                            ),
                            (
                                "BOTTOMPADDING",
                                (
                                    0,
                                    0,
                                ),
                                (
                                    -1,
                                    -1,
                                ),
                                7,
                            ),
                        ]
                    )
                )

                story.append(
                    Spacer(
                        1,
                        7,
                    )
                )

                story.append(
                    image_box
                )
            except Exception:
                story.append(
                    Paragraph(
                        _pdf_display_text(
                            (
                                "L'image n'a pas pu être rendue "
                                "dans le rapport."
                                if not is_rtl
                                else (
                                    "تعذر عرض الصورة "
                                    "داخل التقرير."
                                )
                            ),
                            rtl=is_rtl,
                        ),
                        small_style,
                    )
                )

        # ----------------------------------------------------
        # LIEN : URL visible et cliquable
        # ----------------------------------------------------

        if (
            evidence_type
            == "link"
        ):
            url = (
                entry[
                    "url"
                ]
                or "—"
            )

            if url != "—":
                safe_url = html.escape(
                    url,
                    quote=True,
                )

                display_url = html.escape(
                    url
                )

                link_content = (
                    f'<link href="{safe_url}" '
                    f'color="#7048B8">'
                    f'{display_url}</link>'
                )

                story.append(
                    Spacer(
                        1,
                        6,
                    )
                )

                story.append(
                    Paragraph(
                        link_content,
                        link_style,
                    )
                )
            else:
                story.append(
                    Paragraph(
                        "—",
                        body_style,
                    )
                )

        # ----------------------------------------------------
        # NOTE : texte intégral dans le rapport
        # ----------------------------------------------------

        if (
            evidence_type
            == "note"
        ):
            story.append(
                Spacer(
                    1,
                    6,
                )
            )

            story.append(
                Paragraph(
                    _pdf_display_text(
                        entry[
                            "note"
                        ]
                        or "—",
                        rtl=is_rtl,
                    ),
                    body_style,
                )
            )

        # ----------------------------------------------------
        # FICHIER TEXTE : contenu lisible directement
        # ----------------------------------------------------

        if (
            entry[
                "is_text_file"
            ]
            and entry[
                "storage_path"
            ]
            and entry[
                "storage_path"
            ].exists()
        ):
            text_content = (
                _read_text_evidence(
                    entry[
                        "storage_path"
                    ]
                )
            )

            if text_content:
                story.append(
                    Spacer(
                        1,
                        6,
                    )
                )

                story.append(
                    Paragraph(
                        _pdf_display_text(
                            text_content,
                            rtl=is_rtl,
                        ),
                        small_style,
                    )
                )

        # ----------------------------------------------------
        # PDF JUSTIFICATIF : pages annexées au même PDF final
        # ----------------------------------------------------

        if (
            entry[
                "is_pdf"
            ]
        ):
            if entry[
                "pdf_appendable"
            ]:
                message = (
                    "Le document PDF est intégré "
                    "à la fin de ce rapport "
                    f"({entry['pdf_page_count']} page(s))."
                    if not is_rtl
                    else (
                        "تم إدراج مستند PDF "
                        "في نهاية هذا التقرير "
                        f"({entry['pdf_page_count']} صفحة)."
                    )
                )
            else:
                message = (
                    "Le document PDF n'a pas pu être "
                    "intégré automatiquement."
                    if not is_rtl
                    else (
                        "تعذر إدراج مستند PDF "
                        "تلقائيًا."
                    )
                )

            story.append(
                Spacer(
                    1,
                    6,
                )
            )

            story.append(
                Paragraph(
                    _pdf_display_text(
                        message,
                        rtl=is_rtl,
                    ),
                    small_style,
                )
            )

        # ----------------------------------------------------
        # AUTRE TYPE DE FICHIER
        # ----------------------------------------------------

        if (
            evidence_type
            == "file"
            and not entry[
                "is_image"
            ]
            and not entry[
                "is_pdf"
            ]
            and not entry[
                "is_text_file"
            ]
        ):
            message = (
                "Document enregistré dans le dossier : "
                f"{entry['original_filename'] or 'fichier'}"
                ". Ce format ne peut pas être rendu "
                "visuellement dans un PDF."
                if not is_rtl
                else (
                    "المستند المسجل في الملف: "
                    f"{entry['original_filename'] or 'ملف'}"
                    ". لا يمكن عرض هذا النوع "
                    "بشكل مرئي داخل PDF."
                )
            )

            story.append(
                Spacer(
                    1,
                    6,
                )
            )

            story.append(
                Paragraph(
                    _pdf_display_text(
                        message,
                        rtl=is_rtl,
                    ),
                    small_style,
                )
            )

        # ----------------------------------------------------
        # INTÉGRITÉ
        # ----------------------------------------------------

        integrity_text = (
            _integrity_label(
                entry[
                    "integrity_status"
                ],
                rtl=is_rtl,
            )
        )

        hash_value = (
            entry[
                "sha256_calculated"
            ]
            or entry[
                "sha256_recorded"
            ]
        )

        if hash_value:
            integrity_text += (
                f" - SHA-256: "
                f"{hash_value}"
            )

        story.append(
            Spacer(
                1,
                6,
            )
        )

        story.append(
            Paragraph(
                _pdf_display_text(
                    integrity_text,
                    rtl=is_rtl,
                ),
                small_style,
            )
        )

    # ========================================================
    # HISTORIQUE - compact pour éviter une page presque vide
    # ========================================================

    story.append(
        Paragraph(
            _pdf_display_text(
                (
                    "Historique du dossier"
                    if not is_rtl
                    else "سجل الملف"
                ),
                rtl=is_rtl,
            ),
            heading_style,
        )
    )

    history_items = sorted(
        (
            case.history_events
            or []
        ),
        key=lambda item:
            item.created_at,
    )

    if history_items:
        history_cards = []

        for event in history_items:
            event_card = Table(
                [
                    [
                        Paragraph(
                            _pdf_display_text(
                                _format_export_date(
                                    event.created_at
                                ),
                                rtl=is_rtl,
                            ),
                            small_style,
                        )
                    ],
                    [
                        Paragraph(
                            _pdf_display_text(
                                event.event_type,
                                rtl=is_rtl,
                            ),
                            body_style,
                        )
                    ],
                ],
                colWidths=[
                    81 * mm,
                ],
            )

            event_card.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            colors.HexColor(
                                "#FAF8FC"
                            ),
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0.35,
                            colors.HexColor(
                                "#E9E3EC"
                            ),
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                    ]
                )
            )

            history_cards.append(
                event_card
            )

        history_rows = []

        for index in range(
            0,
            len(history_cards),
            2,
        ):
            row = history_cards[
                index:
                index + 2
            ]

            if len(row) == 1:
                row.append("")

            history_rows.append(
                row
            )

        history_grid = Table(
            history_rows,
            colWidths=[
                84 * mm,
                84 * mm,
            ],
        )

        history_grid.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                ]
            )
        )

        story.append(
            history_grid
        )
    else:
        story.append(
            Paragraph(
                _pdf_display_text(
                    (
                        "Aucun événement enregistré."
                        if not is_rtl
                        else "لا توجد أحداث مسجلة."
                    ),
                    rtl=is_rtl,
                ),
                body_style,
            )
        )

    story.append(
        Spacer(
            1,
            7,
        )
    )

    footer_text = (
        "Document généré par EMC Helpline - "
        f"{_format_export_date(generated_at)} - "
        f"Administrateur : {generated_by}"
    )

    if is_rtl:
        footer_text = (
            "وثيقة تم إنشاؤها بواسطة EMC Helpline - "
            f"{_format_export_date(generated_at)} - "
            f"المسؤول: {generated_by}"
        )

    generation_card = Table(
        [
            [
                Paragraph(
                    _pdf_display_text(
                        footer_text,
                        rtl=is_rtl,
                    ),
                    small_style,
                )
            ]
        ],
        colWidths=[
            168 * mm,
        ],
    )

    generation_card.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F4EFFC"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#DED2E8"
                    ),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        generation_card
    )

    page_callback = (
        _platform_pdf_page_callback(
            case_reference=reference,
            regular_font=regular_font,
            bold_font=bold_font,
        )
    )

    document.build(
        story,
        onFirstPage=page_callback,
        onLaterPages=page_callback,
    )

    return buffer.getvalue()


def _build_pdf_appendix_separator(
    *,
    case: Case,
    entry: dict,
) -> bytes:
    buffer = io.BytesIO()

    (
        regular_font,
        bold_font,
    ) = _pdf_font_names()

    is_rtl = (
        case.language
        == "ar"
    )

    align = (
        TA_RIGHT
        if is_rtl
        else TA_LEFT
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AppendixTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=19,
        leading=24,
        textColor=colors.HexColor(
            "#2B185D"
        ),
        alignment=align,
    )

    body_style = ParagraphStyle(
        "AppendixBody",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=10,
        leading=15,
        textColor=colors.HexColor(
            "#5C5365"
        ),
        alignment=align,
    )

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=31 * mm,
        bottomMargin=23 * mm,
    )

    reference = (
        f"#{str(case.id)[:8].upper()}"
    )

    story = [
        Paragraph(
            _pdf_display_text(
                (
                    "Annexe de preuve PDF"
                    if not is_rtl
                    else "ملحق دليل PDF"
                ),
                rtl=is_rtl,
            ),
            title_style,
        ),
        Spacer(
            1,
            14,
        ),
        Paragraph(
            _pdf_display_text(
                (
                    f"Dossier {reference}"
                    if not is_rtl
                    else f"الملف {reference}"
                ),
                rtl=is_rtl,
            ),
            body_style,
        ),
        Spacer(
            1,
            7,
        ),
        Paragraph(
            _pdf_display_text(
                (
                    f"Preuve {entry['index']} : "
                    f"{entry['title']}"
                    if not is_rtl
                    else (
                        f"الدليل {entry['index']}: "
                        f"{entry['title']}"
                    )
                ),
                rtl=is_rtl,
            ),
            body_style,
        ),
        Spacer(
            1,
            7,
        ),
        Paragraph(
            _pdf_display_text(
                (
                    "Les pages suivantes correspondent "
                    "au document justificatif original."
                    if not is_rtl
                    else (
                        "الصفحات التالية هي صفحات "
                        "المستند الأصلي الداعم."
                    )
                ),
                rtl=is_rtl,
            ),
            body_style,
        ),
    ]

    callback = (
        _platform_pdf_page_callback(
            case_reference=reference,
            regular_font=regular_font,
            bold_font=bold_font,
        )
    )

    document.build(
        story,
        onFirstPage=callback,
        onLaterPages=callback,
    )

    return buffer.getvalue()


def _build_complete_case_pdf(
    *,
    case: Case,
    victim_identity: dict,
    generated_by: User,
) -> tuple[
    Path,
    str,
    int,
]:
    generated_at = datetime.now(
        timezone.utc
    )

    evidence_entries = (
        _prepare_evidence_entries(
            case
        )
    )

    base_report = (
        _build_case_report_pdf(
            case=case,
            victim_identity=(
                victim_identity
            ),
            generated_by=(
                generated_by.username
            ),
            generated_at=(
                generated_at
            ),
            evidence_entries=(
                evidence_entries
            ),
        )
    )

    writer = PdfWriter()

    base_reader = PdfReader(
        io.BytesIO(
            base_report
        )
    )

    for page in (
        base_reader.pages
    ):
        writer.add_page(
            page
        )

    # Les documents PDF justificatifs sont ajoutés
    # comme annexes dans LE MÊME PDF final.
    for entry in evidence_entries:
        if not (
            entry[
                "is_pdf"
            ]
            and entry[
                "pdf_appendable"
            ]
            and entry[
                "storage_path"
            ]
        ):
            continue

        separator_pdf = (
            _build_pdf_appendix_separator(
                case=case,
                entry=entry,
            )
        )

        separator_reader = PdfReader(
            io.BytesIO(
                separator_pdf
            )
        )

        for page in (
            separator_reader.pages
        ):
            writer.add_page(
                page
            )

        try:
            source_reader = PdfReader(
                str(
                    entry[
                        "storage_path"
                    ]
                )
            )

            if source_reader.is_encrypted:
                try:
                    source_reader.decrypt(
                        ""
                    )
                except Exception:
                    continue

            for page in (
                source_reader.pages
            ):
                writer.add_page(
                    page
                )
        except Exception:
            # La preuve reste décrite dans la partie principale
            # même si ses pages ne peuvent pas être annexées.
            continue

    fd, temp_name = (
        tempfile.mkstemp(
            suffix=".pdf"
        )
    )

    os.close(fd)

    output_path = Path(
        temp_name
    )

    try:
        with output_path.open(
            "wb"
        ) as output_file:
            writer.write(
                output_file
            )
    except Exception:
        output_path.unlink(
            missing_ok=True
        )
        raise

    download_name = (
        "Dossier_EMC_"
        f"{str(case.id)[:8].upper()}_"
        f"{generated_at.strftime('%Y-%m-%d')}"
        ".pdf"
    )

    return (
        output_path,
        download_name,
        len(
            evidence_entries
        ),
    )


def _cleanup_export(
    path: Path,
):
    path.unlink(
        missing_ok=True
    )


def _collect_case_evidence_paths(
    *,
    case_id: uuid.UUID,
    db: Session,
) -> list[Path]:
    values = db.scalars(
        select(
            Evidence.storage_path
        )
        .where(
            Evidence.case_id == case_id,
            Evidence.storage_path.is_not(None),
        )
    ).all()

    return [
        Path(value)
        for value in values
        if value
    ]


def _cleanup_deleted_case_files(
    paths: list[Path],
) -> None:
    for path in paths:
        try:
            path.unlink(
                missing_ok=True
            )
        except OSError:
            pass


def _record_first_admin_view(
    *,
    case: Case,
    admin: User,
    db: Session,
) -> None:
    """
    Journalise uniquement la première ouverture explicite du dossier
    par l'équipe administrative.

    Le but est d'informer la victime que son dossier a bien été
    consulté, sans créer un nouvel événement à chaque réouverture
    ou rafraîchissement de la page.
    """

    already_viewed = db.scalar(
        select(
            HistoryEvent.id
        )
        .where(
            HistoryEvent.case_id
            == case.id,
            HistoryEvent.event_type
            == "case_viewed_by_admin",
        )
        .limit(1)
    )

    if already_viewed is not None:
        return

    event = HistoryEvent(
        case_id=case.id,
        actor_user_id=admin.id,
        event_type="case_viewed_by_admin",
        event_data={
            "viewed_by":
                "emc_team",
            "first_view":
                True,
        },
    )

    db.add(
        event
    )

    db.commit()


@router.get(
    "/admin/cases",
    response_model=AdminCasesPublic,
)
def list_admin_cases(
    q: str | None = Query(
        default=None,
        max_length=100,
    ),
    case_status: str | None = Query(
        default=None,
        alias="status",
    ),
    language: str | None = Query(
        default=None,
    ),
    emergency: bool | None = Query(
        default=None,
    ),
    intent: str | None = Query(
        default=None,
        max_length=100,
    ),
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminCasesPublic:

    # ========================================================
    # SUMMARY — TOUJOURS GLOBAL
    # ========================================================

    total_cases = int(
        db.scalar(
            select(
                func.count(
                    Case.id
                )
            )
        )
        or 0
    )

    active_cases = int(
        db.scalar(
            select(
                func.count(
                    Case.id
                )
            ).where(
                Case.status
                == CaseStatus.active
            )
        )
        or 0
    )

    closed_cases = int(
        db.scalar(
            select(
                func.count(
                    Case.id
                )
            ).where(
                Case.status
                == CaseStatus.closed
            )
        )
        or 0
    )

    priority_cases = int(
        db.scalar(
            select(
                func.count(
                    Case.id
                )
            ).where(
                Case.status
                == CaseStatus.active,
                Case.emergency.is_(
                    True
                ),
            )
        )
        or 0
    )

    # ========================================================
    # FILTERS
    # ========================================================

    statement = (
        _base_case_query()
        .order_by(
            Case.updated_at.desc()
        )
    )

    clean_q = (
        q.strip()
        if q
        else ""
    )

    if clean_q:
        pattern = (
            f"%{clean_q}%"
        )

        statement = (
            statement.where(
                or_(
                    User.username.ilike(
                        pattern
                    ),
                    Case.detected_intent.ilike(
                        pattern
                    ),
                )
            )
        )

    if case_status:
        if case_status not in {
            "active",
            "closed",
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Statut invalide."
                ),
            )

        statement = (
            statement.where(
                Case.status
                == CaseStatus(
                    case_status
                )
            )
        )

    if language:
        if language not in {
            "fr",
            "ar",
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "Langue invalide."
                ),
            )

        statement = (
            statement.where(
                Case.language
                == language
            )
        )

    if emergency is not None:
        statement = (
            statement.where(
                Case.emergency.is_(
                    emergency
                )
            )
        )

    if intent:
        statement = (
            statement.where(
                Case.detected_intent
                == intent
            )
        )

    cases = list(
        db.scalars(
            statement
        ).all()
    )

    # ========================================================
    # INTENTS DISPONIBLES
    # ========================================================

    intent_rows = db.scalars(
        select(
            Case.detected_intent
        )
        .where(
            Case.detected_intent
            .is_not(None)
        )
        .distinct()
        .order_by(
            Case.detected_intent
        )
    ).all()

    intents = [
        str(value)
        for value
        in intent_rows
        if value
    ]

    items = [
        _to_list_item(
            case,
            db,
        )
        for case
        in cases
    ]

    return AdminCasesPublic(
        summary=AdminCasesSummary(
            total_cases=(
                total_cases
            ),
            active_cases=(
                active_cases
            ),
            closed_cases=(
                closed_cases
            ),
            priority_cases=(
                priority_cases
            ),
        ),
        items=items,
        filtered_count=len(
            items
        ),
        intents=intents,
    )


@router.get(
    "/admin/cases/{case_id}",
    response_model=AdminCaseDetail,
)
def get_admin_case(
    case_id: uuid.UUID,
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminCaseDetail:

    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    _record_first_admin_view(
        case=case,
        admin=current_user,
        db=db,
    )

    # Recharge le dossier afin que l'historique en mémoire
    # reflète immédiatement l'événement nouvellement créé.
    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    return _to_detail(
        case,
        db,
    )


@router.post(
    "/admin/cases/{case_id}/export",
)
def export_admin_case(
    case_id: uuid.UUID,
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    _: None = Depends(
        verify_csrf
    ),
    db: Session = Depends(
        get_db
    ),
):
    """
    Génère un PDF unique contenant le dossier complet.

    Le rapport contient directement :
    - la situation déclarée ;
    - le plan d'action ;
    - les captures/images ;
    - les notes ;
    - les liens cliquables ;
    - les fichiers texte lisibles ;
    - les informations d'intégrité SHA-256 ;
    - l'historique.

    Les preuves PDF sont ajoutées en annexe dans le même fichier PDF.
    """

    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    victim_identity = _victim_identity(
        case,
        db,
    )

    try:
        (
            pdf_path,
            download_name,
            evidence_count,
        ) = _build_complete_case_pdf(
            case=case,
            victim_identity=(
                victim_identity
            ),
            generated_by=(
                current_user
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Impossible de générer "
                "le PDF complet du dossier."
            ),
        ) from exc

    history_event = HistoryEvent(
        case_id=case.id,
        actor_user_id=(
            current_user.id
        ),
        event_type=(
            "case_exported"
        ),
        event_data={
            "format":
                "pdf",
            "evidence_count":
                evidence_count,
            "generated_by":
                "admin",
        },
    )

    db.add(
        history_event
    )

    db.commit()

    return FileResponse(
        path=str(
            pdf_path
        ),
        media_type=(
            "application/pdf"
        ),
        filename=(
            download_name
        ),
        background=BackgroundTask(
            _cleanup_export,
            pdf_path,
        ),
    )


@router.patch(
    "/admin/cases/{case_id}/deletion-request",
    response_model=AdminDeletionRequestResult,
)
def decide_admin_case_deletion_request(
    case_id: uuid.UUID,
    payload: AdminDeletionRequestDecision,
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    _: None = Depends(
        verify_csrf
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminDeletionRequestResult:
    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    pending, _ = _deletion_request_state(
        case_id=case.id,
        db=db,
    )

    if not pending:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Aucune demande de suppression en attente pour ce dossier."
            ),
        )

    if payload.decision == "reject":
        event = HistoryEvent(
            case_id=case.id,
            actor_user_id=current_user.id,
            event_type="case_deletion_rejected",
            event_data={
                "decision_by":
                    "admin",
            },
        )

        try:
            db.add(event)
            db.commit()
        except Exception:
            db.rollback()
            raise

        return AdminDeletionRequestResult(
            case_id=case.id,
            outcome="rejected",
            message=(
                "La demande de suppression a été refusée."
            ),
        )

    evidence_paths = _collect_case_evidence_paths(
        case_id=case.id,
        db=db,
    )

    deleted_case_id = case.id

    try:
        db.delete(case)
        db.commit()
    except Exception:
        db.rollback()
        raise

    _cleanup_deleted_case_files(
        evidence_paths
    )

    return AdminDeletionRequestResult(
        case_id=deleted_case_id,
        outcome="deleted",
        message=(
            "La demande a été acceptée et le dossier a été supprimé définitivement."
        ),
    )


@router.get(
    "/admin/cases/{case_id}/evidence/{evidence_id}",
    response_model=AdminEvidenceDetail,
)
def get_admin_case_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminEvidenceDetail:

    # Vérifie d'abord que le dossier existe.
    _load_admin_case(
        case_id=case_id,
        db=db,
    )

    evidence = _load_admin_evidence(
        case_id=case_id,
        evidence_id=evidence_id,
        db=db,
    )

    return _to_evidence_detail(
        evidence
    )


@router.get(
    "/admin/cases/{case_id}/evidence/{evidence_id}/download",
)
def download_admin_case_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    db: Session = Depends(
        get_db
    ),
):
    """
    Téléchargement / consultation d'un fichier de preuve par un admin.

    Le storage_path n'est jamais retourné au frontend.
    """

    _load_admin_case(
        case_id=case_id,
        db=db,
    )

    evidence = _load_admin_evidence(
        case_id=case_id,
        evidence_id=evidence_id,
        db=db,
    )

    evidence_type = (
        _evidence_type_value(
            evidence.type
        )
    )

    if evidence_type not in {
        "file",
        "screenshot",
    }:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Cette preuve ne contient "
                "pas de fichier."
            ),
        )

    if not evidence.storage_path:
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


@router.patch(
    "/admin/cases/{case_id}/workflow-status",
    response_model=AdminCaseDetail,
)
def update_admin_case_workflow_status(
    case_id: uuid.UUID,
    payload: AdminCaseWorkflowStatusUpdate,
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    _: None = Depends(
        verify_csrf
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminCaseDetail:
    """
    Met à jour l'étape métier de prise en charge d'un dossier.

    Règles de cohérence :
    - workflow_status = closed -> status technique = closed ;
    - tout autre workflow_status -> status technique = active.

    Chaque changement est journalisé afin d'être visible
    dans l'historique de la victime.
    """

    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    new_workflow_status = (
        CaseWorkflowStatus(
            payload.workflow_status
        )
    )

    old_workflow_status = (
        case.workflow_status
    )

    old_case_status = (
        case.status
    )

    target_case_status = (
        CaseStatus.closed
        if new_workflow_status
        == CaseWorkflowStatus.closed
        else CaseStatus.active
    )

    if (
        old_workflow_status
        != new_workflow_status
        or old_case_status
        != target_case_status
    ):
        case.workflow_status = (
            new_workflow_status
        )

        case.status = (
            target_case_status
        )

        history_event = HistoryEvent(
            case_id=case.id,
            actor_user_id=(
                current_user.id
            ),
            event_type=(
                "case_workflow_status_changed"
            ),
            event_data={
                "old_workflow_status":
                    _workflow_status_value(
                        old_workflow_status
                    ),
                "new_workflow_status":
                    _workflow_status_value(
                        new_workflow_status
                    ),
                "old_status":
                    _status_value(
                        old_case_status
                    ),
                "new_status":
                    _status_value(
                        target_case_status
                    ),
                "changed_by":
                    "admin",
            },
        )

        try:
            db.add(
                history_event
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    return _to_detail(
        case,
        db,
    )


@router.patch(
    "/admin/cases/{case_id}/status",
    response_model=AdminCaseDetail,
)
def update_admin_case_status(
    case_id: uuid.UUID,
    payload: AdminCaseStatusUpdate,
    current_user: User = Depends(
        require_role(
            UserRole.admin
        )
    ),
    _: None = Depends(
        verify_csrf
    ),
    db: Session = Depends(
        get_db
    ),
) -> AdminCaseDetail:

    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    new_status = CaseStatus(
        payload.status
    )

    old_status = (
        case.status
    )

    if old_status != new_status:
        case.status = new_status

        # Compatibilité avec l'ancienne gestion active/closed.
        # Si l'admin utilise encore cette route technique,
        # le workflow reste cohérent.
        if new_status == CaseStatus.closed:
            case.workflow_status = (
                CaseWorkflowStatus.closed
            )
        elif (
            case.workflow_status
            == CaseWorkflowStatus.closed
        ):
            case.workflow_status = (
                CaseWorkflowStatus.new
            )

        history_event = (
            HistoryEvent(
                case_id=case.id,
                actor_user_id=(
                    current_user.id
                ),
                event_type=(
                    "case_status_changed"
                ),
                event_data={
                    "old_status":
                        _status_value(
                            old_status
                        ),
                    "new_status":
                        _status_value(
                            new_status
                        ),
                    "changed_by":
                        "admin",
                },
            )
        )

        db.add(
            history_event
        )

        db.commit()

    case = _load_admin_case(
        case_id=case_id,
        db=db,
    )

    return _to_detail(
        case
    )