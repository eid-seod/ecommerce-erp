"""Money and quantity conversion helpers."""
from decimal import ROUND_HALF_UP, Decimal

SCALE = Decimal(10000)
def to_db(value): return int((Decimal(str(value)) * SCALE).quantize(Decimal(1), rounding=ROUND_HALF_UP))
def from_db(value): return (Decimal(value or 0) / SCALE).quantize(Decimal('0.0001'))
