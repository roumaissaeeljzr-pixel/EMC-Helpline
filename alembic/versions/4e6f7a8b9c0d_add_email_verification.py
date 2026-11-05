"""add email verification

Revision ID: 4e6f7a8b9c0d
Revises: 3d4e5f6a7b8c
Create Date: 2026-08-28 05:45:00
"""

from typing import (
    Sequence,
    Union,
)

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "4e6f7a8b9c0d"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "3d4e5f6a7b8c"

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
    # Les comptes déjà présents sont conservés comme utilisables
    # afin de ne pas bloquer les comptes de développement existants.
    # Les NOUVEAUX comptes créés après cette migration auront
    # email_verified = false jusqu'à saisie du code reçu par e-mail.
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "email_verified_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE users
        SET email_verified = true
        """
    )

    op.create_table(
        "email_verification_codes",

        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),

        sa.Column(
            "code_hash",
            sa.String(
                length=64
            ),
            nullable=False,
        ),

        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),

        sa.Column(
            "used_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
            server_default=sa.text(
                "now()"
            ),
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_email_verification_codes_user_id",
        "email_verification_codes",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_email_verification_codes_expires_at",
        "email_verification_codes",
        [
            "expires_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_email_verification_codes_created_at",
        "email_verification_codes",
        [
            "created_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_email_verification_codes_created_at",
        table_name="email_verification_codes",
    )

    op.drop_index(
        "ix_email_verification_codes_expires_at",
        table_name="email_verification_codes",
    )

    op.drop_index(
        "ix_email_verification_codes_user_id",
        table_name="email_verification_codes",
    )

    op.drop_table(
        "email_verification_codes"
    )

    op.drop_column(
        "users",
        "email_verified_at",
    )

    op.drop_column(
        "users",
        "email_verified",
    )
