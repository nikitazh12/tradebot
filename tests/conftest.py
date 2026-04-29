from datetime import UTC, datetime
from decimal import Decimal

import pytest


@pytest.fixture
def utc_now() -> datetime:
    return datetime(2024, 6, 1, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_price() -> Decimal:
    return Decimal("285.50")
