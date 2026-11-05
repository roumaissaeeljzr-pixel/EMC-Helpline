"""
db/models.py

Modèles SQLAlchemy 2.x pour EMC Helpline.

Relations principales :
    User (1) ──< (N) Case
    User (1) ──< (N) PasswordResetCode
    User (1) ──< (N) EmailVerificationCode
    User (1) ──< (N) HistoryEvent

    Case (1) ── (0..1) ActionPlan
    Case (1) ──< (N) Evidence
    Case (1) ──< (N) HistoryEvent

    ActionPlan (1) ──< (N) ActionItem
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy import Enum as SAEnum
from sqlalchemy import func

from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from db.database import Base


# ============================================================
# ENUMS
# ============================================================

class UserRole(str, enum.Enum):
    victim = "victim"
    admin = "admin"


class CaseStatus(str, enum.Enum):
    active = "active"
    closed = "closed"


class CaseWorkflowStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    waiting_information = "waiting_information"
    resolved = "resolved"
    closed = "closed"


class EvidenceType(str, enum.Enum):
    screenshot = "screenshot"
    file = "file"
    link = "link"
    note = "note"


# ============================================================
# USER
# ============================================================

class User(Base):

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
        ),
        nullable=False,
        default=UserRole.victim,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # L'adresse e-mail doit être confirmée par un code reçu
    # dans la boîte indiquée lors de l'inscription.
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    email_verified_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ========================================================
    # RELATIONS
    # ========================================================

    cases: Mapped[
        list["Case"]
    ] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    password_reset_codes: Mapped[
        list["PasswordResetCode"]
    ] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    email_verification_codes: Mapped[
        list["EmailVerificationCode"]
    ] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    history_events: Mapped[
        list["HistoryEvent"]
    ] = relationship(
        back_populates="actor",
        foreign_keys="HistoryEvent.actor_user_id",
    )

    def __repr__(self) -> str:

        return (
            f"<User id={self.id} "
            f"username={self.username!r} "
            f"role={self.role.value}>"
        )


# ============================================================
# EMAIL VERIFICATION CODE
# ============================================================

class EmailVerificationCode(Base):

    __tablename__ = "email_verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Empreinte uniquement : le code à 6 chiffres n'est jamais
    # conservé en clair dans PostgreSQL.
    code_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="email_verification_codes",
    )

    def __repr__(self) -> str:

        return (
            f"<EmailVerificationCode id={self.id} "
            f"user_id={self.user_id} "
            f"attempts={self.attempts}>"
        )


# ============================================================
# PASSWORD RESET CODE
# ============================================================

class PasswordResetCode(Base):

    __tablename__ = "password_reset_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    code_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="password_reset_codes",
    )

    def __repr__(self) -> str:

        return (
            f"<PasswordResetCode id={self.id} "
            f"user_id={self.user_id} "
            f"attempts={self.attempts}>"
        )


# ============================================================
# CASE
# ============================================================

class Case(Base):

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    detected_intent: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    language: Mapped[
        str | None
    ] = mapped_column(
        String(2),
        nullable=True,
    )

    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(
            CaseStatus,
            name="case_status",
        ),
        nullable=False,
        default=CaseStatus.active,
    )

    # Statut métier de prise en charge.
    #
    # `status` reste le statut technique du dossier (active / closed)
    # afin de préserver la compatibilité avec les routes existantes.
    #
    # `workflow_status` décrit l'avancement réel du traitement :
    # new -> in_progress -> waiting_information -> resolved -> closed.
    workflow_status: Mapped[
        CaseWorkflowStatus
    ] = mapped_column(
        SAEnum(
            CaseWorkflowStatus,
            name="case_workflow_status",
        ),
        nullable=False,
        default=CaseWorkflowStatus.new,
        server_default="new",
        index=True,
    )

    emergency: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ========================================================
    # RELATIONS
    # ========================================================

    user: Mapped["User"] = relationship(
        back_populates="cases",
    )

    action_plan: Mapped[
        "ActionPlan | None"
    ] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )

    evidences: Mapped[
        list["Evidence"]
    ] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="Evidence.created_at.desc()",
    )

    history_events: Mapped[
        list["HistoryEvent"]
    ] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="HistoryEvent.created_at.desc()",
    )

    def __repr__(self) -> str:

        return (
            f"<Case id={self.id} "
            f"user_id={self.user_id} "
            f"status={self.status.value} "
            f"workflow_status={self.workflow_status.value}>"
        )


# ============================================================
# EVIDENCE
# ============================================================

class Evidence(Base):

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    type: Mapped[EvidenceType] = mapped_column(
        SAEnum(
            EvidenceType,
            name="evidence_type",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ========================================================
    # SCREENSHOT / FILE
    # ========================================================

    original_filename: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )

    stored_filename: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )

    storage_path: Mapped[
        str | None
    ] = mapped_column(
        String(1024),
        nullable=True,
    )

    mime_type: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )

    file_size: Mapped[
        int | None
    ] = mapped_column(
        BigInteger,
        nullable=True,
    )

    sha256: Mapped[
        str | None
    ] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    # ========================================================
    # LINK
    # ========================================================

    url: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # NOTE
    # ========================================================

    note: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # DATES
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ========================================================
    # RELATION
    # ========================================================

    case: Mapped["Case"] = relationship(
        back_populates="evidences",
    )

    def __repr__(self) -> str:

        return (
            f"<Evidence id={self.id} "
            f"case_id={self.case_id} "
            f"type={self.type.value}>"
        )


# ============================================================
# HISTORY EVENT
# ============================================================

class HistoryEvent(Base):

    __tablename__ = "history_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ========================================================
    # DOSSIER CONCERNÉ
    # ========================================================

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # UTILISATEUR À L'ORIGINE DE L'ACTION
    # ========================================================

    actor_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================
    # TYPE D'ÉVÉNEMENT
    # ========================================================
    #
    # Exemples :
    #
    # case_created
    # assessment_completed
    # action_plan_generated
    # action_completed
    # action_reopened
    # evidence_added
    # evidence_deleted
    # case_status_changed
    #
    # ========================================================

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # ========================================================
    # DONNÉES COMPLÉMENTAIRES
    # ========================================================
    #
    # Exemple :
    #
    # {
    #     "evidence_id": "...",
    #     "evidence_type": "screenshot",
    #     "title": "Capture Instagram"
    # }
    #
    # ========================================================

    event_data: Mapped[
        dict | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ========================================================
    # DATE
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # ========================================================
    # RELATIONS
    # ========================================================

    case: Mapped["Case"] = relationship(
        back_populates="history_events",
    )

    actor: Mapped[
        "User | None"
    ] = relationship(
        back_populates="history_events",
        foreign_keys=[actor_user_id],
    )

    def __repr__(self) -> str:

        return (
            f"<HistoryEvent id={self.id} "
            f"case_id={self.case_id} "
            f"event_type={self.event_type!r}>"
        )


# ============================================================
# ACTION PLAN
# ============================================================

class ActionPlan(Base):

    __tablename__ = "action_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cases.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    detected_intent: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    case: Mapped["Case"] = relationship(
        back_populates="action_plan",
    )

    items: Mapped[
        list["ActionItem"]
    ] = relationship(
        back_populates="action_plan",
        cascade="all, delete-orphan",
        order_by="ActionItem.position",
    )

    def __repr__(self) -> str:

        return (
            f"<ActionPlan id={self.id} "
            f"case_id={self.case_id}>"
        )


# ============================================================
# ACTION ITEM
# ============================================================

class ActionItem(Base):

    __tablename__ = "action_items"

    __table_args__ = (
        UniqueConstraint(
            "action_plan_id",
            "source_action_id",
            name="uq_action_item_plan_source_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    action_plan_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "action_plans.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    source_action_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[
        dict | None
    ] = mapped_column(
        JSONB,
        nullable=True,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    completed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    action_plan: Mapped[
        "ActionPlan"
    ] = relationship(
        back_populates="items",
    )

    def __repr__(self) -> str:

        return (
            f"<ActionItem id={self.id} "
            f"action_plan_id={self.action_plan_id} "
            f"completed={self.completed}>"
        )
# ============================================================
# RESOURCE
# ============================================================

class Resource(Base):

    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Exemple :
    # account, evidence, harassment, privacy,
    # identity, images, legal, report, emergency
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # ========================================================
    # TITRES
    # ========================================================

    title_fr: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    title_ar: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ========================================================
    # DESCRIPTIONS COURTES
    # ========================================================

    description_fr: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    description_ar: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ========================================================
    # CONTENU DÉTAILLÉ
    # ========================================================

    content_fr: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content_ar: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ========================================================
    # POINTS / CONSEILS
    #
    # Exemple :
    # [
    #   "Modifier le mot de passe",
    #   "Vérifier les sessions actives"
    # ]
    # ========================================================

    points_fr: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    points_ar: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # ========================================================
    # APPARENCE FRONTEND
    # ========================================================

    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    tone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ========================================================
    # PUBLICATION
    #
    # draft     -> visible uniquement par l'admin
    # published -> visible par la victime
    # ========================================================

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )

    # Ordre d'affichage dans la page Ressources.
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # ADMIN CRÉATEUR
    # ========================================================

    created_by: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================
    # DATES
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Resource id={self.id} "
            f"category={self.category!r} "
            f"status={self.status!r}>"
        )