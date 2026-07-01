"""Default evaluation bands seeded per user at registration.

Half-open intervals [lower, upper): None = -inf / +inf.
Percentage indicators store percent values (e.g. 10 == 10%).
`reliability` is a raw tournament count, not a percentage.

These are defaults only — users edit their own bands afterward; nothing here
is hardcoded into the classification logic.
"""

from decimal import Decimal

# (indicator_key, [(lower, upper, label), ...]) — order = range_order ascending
DEFAULT_EVALUATION_RANGES: dict[str, list[tuple[Decimal | None, Decimal | None, str]]] = {
    "roi": [
        (None, Decimal("0"), "Perdedor"),
        (Decimal("0"), Decimal("10"), "Regular"),
        (Decimal("10"), Decimal("30"), "Bom"),
        (Decimal("30"), None, "Excelente"),
    ],
    "itm": [
        (None, Decimal("12"), "Baixo"),
        (Decimal("12"), Decimal("15"), "Regular"),
        (Decimal("15"), Decimal("20"), "Bom"),
        (Decimal("20"), None, "Excelente"),
    ],
    "final_table_pct": [
        (None, Decimal("1"), "Baixa"),
        (Decimal("1"), Decimal("2"), "Regular"),
        (Decimal("2"), Decimal("4"), "Boa"),
        (Decimal("4"), None, "Excelente"),
    ],
    "win_pct": [
        (None, Decimal("0.2"), "Baixa"),
        (Decimal("0.2"), Decimal("0.5"), "Regular"),
        (Decimal("0.5"), Decimal("1"), "Boa"),
        (Decimal("1"), None, "Excelente"),
    ],
    # tournament-count thresholds; upper bound exclusive
    "reliability": [
        (None, Decimal("101"), "Muito Baixa"),
        (Decimal("101"), Decimal("301"), "Baixa"),
        (Decimal("301"), Decimal("501"), "Moderada"),
        (Decimal("501"), Decimal("1001"), "Boa"),
        (Decimal("1001"), None, "Alta"),
    ],
}
