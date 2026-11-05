"""
create evidence table

Revision ID: b73c6e4a912f
Revises: 8e0d7a31b6f2
Create Date: 2026-08-20
"""

from typing import (
    Sequence,
    Union,
)

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import (
    postgresql,
)


revision: str = "b73c6e4a912f"

down_revision: Union[
    str,
    None,
] = "8e0d7a31b6f2"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:

    # ========================================================
    # ENUM evidence_type
    # ========================================================

    evidence_type = postgresql.ENUM(
        "screenshot",
        "file",
        "link",
        "note",
        name="evidence_type",
    )

    evidence_type.create(
        op.get_bind(),
        checkfirst=True,
    )


    # ========================================================
    # TABLE evidence
    # ========================================================

    op.create_table(
        "evidence",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "case_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "type",
            postgresql.ENUM(
                "screenshot",
                "file",
                "link",
                "note",
                name="evidence_type",
                create_type=False,
            ),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(
                length=255
            ),
            nullable=False,
        ),

        # ====================================================
        # FICHIERS
        # ====================================================

        sa.Column(
            "original_filename",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        sa.Column(
            "stored_filename",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        sa.Column(
            "storage_path",
            sa.String(
                length=1024
            ),
            nullable=True,
        ),

        sa.Column(
            "mime_type",
            sa.String(
                length=255
            ),
            nullable=True,
        ),

        sa.Column(
            "file_size",
            sa.BigInteger(),
            nullable=True,
        ),

        sa.Column(
            "sha256",
            sa.String(
                length=64
            ),
            nullable=True,
        ),

        # ====================================================
        # LIEN
        # ====================================================

        sa.Column(
            "url",
            sa.Text(),
            nullable=True,
        ),

        # ====================================================
        # NOTE
        # ====================================================

        sa.Column(
            "note",
            sa.Text(),
            nullable=True,
        ),

        # ====================================================
        # DATES
        # ====================================================

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.text(
                "now()"
            ),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            server_default=sa.text(
                "now()"
            ),
            nullable=False,
        ),

        # ====================================================
        # FOREIGN KEY
        # ====================================================

        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )


    # ========================================================
    # INDEXES
    # ========================================================

    op.create_index(
        "ix_evidence_case_id",
        "evidence",
        ["case_id"],
        unique=False,
    )

    op.create_index(
        "ix_evidence_type",
        "evidence",
        ["type"],
        unique=False,
    )

    op.create_index(
        "ix_evidence_sha256",
        "evidence",
        ["sha256"],
        unique=False,
    )

    op.create_index(
        "ix_evidence_created_at",
        "evidence",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:

    # ========================================================
    # INDEXES
    # ========================================================

    op.drop_index(
        "ix_evidence_created_at",
        table_name="evidence",
    )

    op.drop_index(
        "ix_evidence_sha256",
        table_name="evidence",
    )

    op.drop_index(
        "ix_evidence_type",
        table_name="evidence",
    )

    op.drop_index(
        "ix_evidence_case_id",
        table_name="evidence",
    )


    # ========================================================
    # TABLE
    # ========================================================

    op.drop_table(
        "evidence"
    )


    # ========================================================
    # ENUM
    # ========================================================

    evidence_type = postgresql.ENUM(
        "screenshot",
        "file",
        "link",
        "note",
        name="evidence_type",
    )

    evidence_type.drop(
        op.get_bind(),
        checkfirst=True,
    )