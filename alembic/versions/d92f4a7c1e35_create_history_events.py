"""
create history events table

Revision ID: d92f4a7c1e35
Revises: b73c6e4a912f
Create Date: 2026-08-21
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


revision: str = "d92f4a7c1e35"

down_revision: Union[
    str,
    None,
] = "b73c6e4a912f"

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
        "history_events",

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
            "actor_user_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=True,
        ),

        sa.Column(
            "event_type",
            sa.String(
                length=50
            ),
            nullable=False,
        ),

        sa.Column(
            "event_data",
            postgresql.JSONB(
                astext_type=sa.Text()
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
            ["case_id"],
            ["cases.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )


    op.create_index(
        "ix_history_events_case_id",
        "history_events",
        ["case_id"],
        unique=False,
    )


    op.create_index(
        "ix_history_events_actor_user_id",
        "history_events",
        ["actor_user_id"],
        unique=False,
    )


    op.create_index(
        "ix_history_events_event_type",
        "history_events",
        ["event_type"],
        unique=False,
    )


    op.create_index(
        "ix_history_events_created_at",
        "history_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_history_events_created_at",
        table_name="history_events",
    )

    op.drop_index(
        "ix_history_events_event_type",
        table_name="history_events",
    )

    op.drop_index(
        "ix_history_events_actor_user_id",
        table_name="history_events",
    )

    op.drop_index(
        "ix_history_events_case_id",
        table_name="history_events",
    )

    op.drop_table(
        "history_events"
    )