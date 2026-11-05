"""
db/victim_profile_model.py

Données d'identité séparées du modèle d'authentification User.

Objectifs :
- ne pas mélanger les champs sensibles avec /auth/me ;
- conserver une relation 1:1 avec users ;
- stocker la CIN uniquement sous forme chiffrée ;
- supprimer automatiquement le profil si le compte est supprimé.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class VictimProfile(Base):
    __tablename__ = "victim_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # Ne jamais stocker la CIN en clair.
    cin_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Permet l'affichage masqué sans déchiffrer la CIN.
    cin_last4: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
    )

    # "Renseignée" et non "vérifiée" :
    # aucune vérification officielle n'est simulée.
    identity_completed_at: Mapped[datetime | None] = mapped_column(
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
