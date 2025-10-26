"""Add user verification and consent fields

Revision ID: 82d758b7d904
Revises: 82d758b7d903
Create Date: 2025-10-26 21:45:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "82d758b7d904"
down_revision = "82d758b7d903"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for verification_status
    verification_status_enum = sa.Enum(
        "pending", "verified", "rejected", "expired", name="verification_status"
    )
    verification_status_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to users table
    op.add_column(
        "users",
        sa.Column(
            "age_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "terms_accepted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "privacy_policy_accepted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "community_guidelines_accepted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("consent_timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users", sa.Column("consent_ip_address", sa.String(45), nullable=True)
    )
    op.add_column("users", sa.Column("terms_version", sa.String(10), nullable=True))
    op.add_column("users", sa.Column("privacy_version", sa.String(10), nullable=True))
    op.add_column(
        "users", sa.Column("guidelines_version", sa.String(10), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "verification_status",
            verification_status_enum,
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    # Remove columns from users table
    op.drop_column("users", "verification_status")
    op.drop_column("users", "guidelines_version")
    op.drop_column("users", "privacy_version")
    op.drop_column("users", "terms_version")
    op.drop_column("users", "consent_ip_address")
    op.drop_column("users", "consent_timestamp")
    op.drop_column("users", "community_guidelines_accepted")
    op.drop_column("users", "privacy_policy_accepted")
    op.drop_column("users", "terms_accepted")
    op.drop_column("users", "age_verified")

    # Drop enum type
    sa.Enum(name="verification_status").drop(op.get_bind(), checkfirst=True)
