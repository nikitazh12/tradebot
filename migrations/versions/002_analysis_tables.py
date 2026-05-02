"""002 analysis tables: indicator_snapshots, detected_levels

Revision ID: 002
Revises: 001
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "indicator_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("figi", sa.String(20), nullable=False),
        sa.Column("tf", sa.String(5), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atr14", sa.Numeric(20, 9), nullable=True),
        sa.Column("ema20", sa.Numeric(20, 9), nullable=True),
        sa.Column("ema50", sa.Numeric(20, 9), nullable=True),
        sa.Column("ema200", sa.Numeric(20, 9), nullable=True),
        sa.Column("rsi14", sa.Numeric(10, 4), nullable=True),
        sa.Column("rel_volume", sa.Numeric(10, 4), nullable=True),
        sa.Column("trend_direction", sa.String(20), nullable=True),
        sa.Column("trend_strength", sa.Numeric(5, 4), nullable=True),
        sa.Column("structure_phase", sa.String(30), nullable=True),
        sa.Column("payload", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index("ix_snapshots_figi_tf_ts", "indicator_snapshots", ["figi", "tf", "ts"])

    op.create_table(
        "detected_levels",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("figi", sa.String(20), nullable=False),
        sa.Column("tf", sa.String(5), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("price", sa.Numeric(20, 9), nullable=False),
        sa.Column("touches", sa.Integer, nullable=False, server_default="1"),
        sa.Column("strength", sa.Numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("first_seen_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index("ix_levels_figi_tf", "detected_levels", ["figi", "tf"])


def downgrade() -> None:
    op.drop_index("ix_levels_figi_tf", table_name="detected_levels")
    op.drop_table("detected_levels")
    op.drop_index("ix_snapshots_figi_tf_ts", table_name="indicator_snapshots")
    op.drop_table("indicator_snapshots")
