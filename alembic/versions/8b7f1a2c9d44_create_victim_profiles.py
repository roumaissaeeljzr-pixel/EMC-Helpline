"""create victim profiles

Revision ID: 8b7f1a2c9d44
Revises: 100f820132cc
Create Date: 2026-08-25

"""

from alembic import op
import sqlalchemy as sa


revision = "8b7f1a2c9d44"
down_revision = "100f820132cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "victim_profiles",

        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "first_name",
            sa.String(
                length=100
            ),
            nullable=True,
        ),

        sa.Column(
            "last_name",
            sa.String(
                length=100
            ),
            nullable=True,
        ),

        sa.Column(
            "date_of_birth",
            sa.Date(),
            nullable=True,
        ),

        sa.Column(
            "phone",
            sa.String(
                length=30
            ),
            nullable=True,
        ),

        sa.Column(
            "cin_encrypted",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "cin_last4",
            sa.String(
                length=4
            ),
            nullable=True,
        ),

        sa.Column(
            "identity_completed_at",
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

        sa.ForeignKeyConstraint(
            [
                "user_id",
            ],
            [
                "users.id",
            ],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "user_id"
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "victim_profiles"
    )
