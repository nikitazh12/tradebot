from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


def quotation_to_decimal(units: int, nano: int) -> Decimal:
    """Конвертирует T-Invest Quotation (units + nano) в Decimal."""
    return Decimal(units) + Decimal(nano) / Decimal("1_000_000_000")


def decimal_to_quotation(value: Decimal) -> tuple[int, int]:
    """Конвертирует Decimal обратно в (units, nano)."""
    units = int(value)
    nano = int((value - Decimal(units)) * Decimal("1_000_000_000"))
    return units, nano


def round_price(price: Decimal, min_increment: Decimal) -> Decimal:
    """Округляет цену до min_price_increment инструмента."""
    if min_increment <= 0:
        return price
    return (price / min_increment).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * min_increment


@dataclass(frozen=True)
class PriceRange:
    low: Decimal
    high: Decimal

    def __post_init__(self) -> None:
        if self.low > self.high:
            raise ValueError(f"PriceRange: low ({self.low}) > high ({self.high})")

    def contains(self, price: Decimal) -> bool:
        return self.low <= price <= self.high

    def midpoint(self) -> Decimal:
        return (self.low + self.high) / 2
