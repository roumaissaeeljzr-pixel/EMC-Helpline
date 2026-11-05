"""add case workflow status

Revision ID: 3d4e5f6a7b8c
Revises: 8b7f1a2c9d44
Create Date: 2026-08-28 05:35:00
"""

from typing import (
    Sequence,
    Union,
)

from alembic import op
import sqlalchemy as sa


revision: str = "3d4e5f6a7b8c"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "8b7f1a2c9d44"

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


case_workflow_status = sa.Enum(
    "new",
    "in_progress",
    "waiting_information",
    "resolved",
    "closed",
    name="case_workflow_status",
)


def upgrade() -> None:
    case_workflow_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.add_column(
        "cases",
        sa.Column(
            "workflow_status",
            case_workflow_status,
            nullable=False,
            server_default="new",
        ),
    )

    op.execute(
        """
        UPDATE cases
        SET workflow_status = 'closed'
        WHERE status = 'closed'
        """
    )

    op.create_index(
        "ix_cases_workflow_status",
        "cases",
        [
            "workflow_status",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cases_workflow_status",
        table_name="cases",
    )

    op.drop_column(
        "cases",
        "workflow_status",
    )

    case_workflow_status.drop(
        op.get_bind(),
        checkfirst=True,
    )
