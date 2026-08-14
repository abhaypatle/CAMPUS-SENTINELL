"""sync current models

Revision ID: ee2dd3742ed5
Revises:
Create Date: 2026-08-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ee2dd3742ed5"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_escalation_events_created_at"),
        "escalation_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_escalation_events_incident_id"),
        "escalation_events",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_reports_created_at"),
        "incident_reports",
        ["created_at"],
        unique=False,
    )

    op.alter_column(
        "recommendations",
        "confidence",
        existing_type=sa.VARCHAR(length=20),
        type_=sa.Float(),
        existing_nullable=True,
    )

    op.create_index(
        op.f("ix_recommendations_created_at"),
        "recommendations",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendations_incident_id"),
        "recommendations",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_assessments_created_at"),
        "risk_assessments",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_assessments_incident_id"),
        "risk_assessments",
        ["incident_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_risk_assessments_incident_id"),
        table_name="risk_assessments",
    )
    op.drop_index(
        op.f("ix_risk_assessments_created_at"),
        table_name="risk_assessments",
    )
    op.drop_index(
        op.f("ix_recommendations_incident_id"),
        table_name="recommendations",
    )
    op.drop_index(
        op.f("ix_recommendations_created_at"),
        table_name="recommendations",
    )

    op.alter_column(
        "recommendations",
        "confidence",
        existing_type=sa.Float(),
        type_=sa.VARCHAR(length=20),
        existing_nullable=True,
    )

    op.drop_index(
        op.f("ix_incident_reports_created_at"),
        table_name="incident_reports",
    )
    op.drop_index(
        op.f("ix_escalation_events_incident_id"),
        table_name="escalation_events",
    )
    op.drop_index(
        op.f("ix_escalation_events_created_at"),
        table_name="escalation_events",
    )