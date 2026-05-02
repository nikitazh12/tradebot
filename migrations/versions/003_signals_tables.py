"""003 signals tables: signals, no_signal_logs

Revision ID: 003
Revises: 002
Create Date: 2026-04-30
"""
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(50), nullable=False),
        sa.Column("figi", sa.String(50), nullable=False),
        sa.Column("tf", sa.String(50), nullable=False),
        sa.Column("direction", sa.String(50), nullable=False),
        sa.Column("setup", sa.String(50), nullable=False),
        sa.Column("entry", sa.Numeric(20, 9), nullable=False),
        sa.Column("stop", sa.Numeric(20, 9), nullable=False),
        sa.Column("take", sa.Numeric(20, 9), nullable=False),
        sa.Column("horizon", sa.String(50), nullable=False),
        sa.Column("risk_level", sa.String(50), nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index("ix_signals_ticker", "signals", ["ticker"])

    op.create_table(
        "no_signal_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(50), nullable=False),
        sa.Column("figi", sa.String(50), nullable=False),
        sa.Column("tf", sa.String(50), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("details", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
    )
    op.create_index("ix_no_signal_logs_ticker", "no_signal_logs", ["ticker"])


def downgrade() -> None:
    op.drop_index("ix_no_signal_logs_ticker", table_name="no_signal_logs")
    op.drop_table("no_signal_logs")
    op.drop_index("ix_signals_ticker", table_name="signals")
    op.drop_table("signals")
