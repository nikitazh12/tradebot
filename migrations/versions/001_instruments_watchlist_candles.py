"""001 instruments watchlist candles

Revision ID: 001
Revises:
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("figi", sa.String(20), primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("instrument_uid", sa.String(50), nullable=False),
        sa.Column("isin", sa.String(20), nullable=False, server_default=""),
        sa.Column("name", sa.String(200), nullable=False, server_default=""),
        sa.Column("class_code", sa.String(10), nullable=False, server_default=""),
        sa.Column("currency", sa.String(10), nullable=False, server_default=""),
        sa.Column("exchange", sa.String(50), nullable=False, server_default=""),
        sa.Column("lot", sa.Integer, nullable=False, server_default="1"),
        sa.Column("min_price_increment", sa.Numeric(20, 9), nullable=False, server_default="0"),
        sa.Column("instrument_type", sa.String(20), nullable=False, server_default="share"),
        sa.Column("trading_status", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.UniqueConstraint("ticker", name="uq_instruments_ticker"),
        sa.UniqueConstraint("instrument_uid", name="uq_instruments_uid"),
    )

    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.UniqueConstraint("ticker", name="uq_watchlist_ticker"),
    )

    op.create_table(
        "candles",
        sa.Column("figi", sa.String(20), nullable=False),
        sa.Column("tf", sa.String(5), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(20, 9), nullable=False),
        sa.Column("high", sa.Numeric(20, 9), nullable=False),
        sa.Column("low", sa.Numeric(20, 9), nullable=False),
        sa.Column("close", sa.Numeric(20, 9), nullable=False),
        sa.Column("volume", sa.BigInteger, nullable=False),
        sa.Column("is_complete", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("figi", "tf", "ts", name="pk_candles"),
    )
    op.create_index("ix_candles_figi_tf_ts", "candles", ["figi", "tf", sa.text("ts DESC")])


def downgrade() -> None:
    op.drop_index("ix_candles_figi_tf_ts", table_name="candles")
    op.drop_table("candles")
    op.drop_table("watchlist")
    op.drop_table("instruments")
