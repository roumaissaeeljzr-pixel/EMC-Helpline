"""
create password reset codes table

Revision ID: 8e0d7a31b6f2
Revises: 21cfc2b76153
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


revision: str = "8e0d7a31b6f2"

down_revision: Union[
    str,
    None,
] = "21cfc2b76153"

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

    op.create_table(
        "password_reset_codes",

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
            server_default="0",
            nullable=False,
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
            server_default=sa.text(
                "now()"
            ),
            nullable=False,
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
        "ix_password_reset_codes_user_id",
        "password_reset_codes",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_password_reset_codes_expires_at",
        "password_reset_codes",
        ["expires_at"],
        unique=False,
    )

    op.create_index(
        "ix_password_reset_codes_created_at",
        "password_reset_codes",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_password_reset_codes_created_at",
        table_name=(
            "password_reset_codes"
        ),
    )

    op.drop_index(
        "ix_password_reset_codes_expires_at",
        table_name=(
            "password_reset_codes"
        ),
    )

    op.drop_index(
        "ix_password_reset_codes_user_id",
        table_name=(
            "password_reset_codes"
        ),
    )

    op.drop_table(
        "password_reset_codes"
    )