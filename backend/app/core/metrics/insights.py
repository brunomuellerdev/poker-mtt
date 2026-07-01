"""Insight engine — turns aggregated stats into calibrated text interpretations.

Design constraint: MTT ROI has very high variance. An insight derived from a
small sample is noise presented as signal, which drives bad decisions. So every
claim tied to a sample carries a reliability label, segment comparisons are
gated by a minimum count, and nothing here claims statistical significance.

Pure functions only — no DB, no I/O. Fully unit-testable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal

# Minimum tournaments for a segment to even enter best/worst-ROI comparisons.
# Below this, ROI is treated as too noisy to name a "best" or "worst".
MIN_SEGMENT_N = 30

_ZERO = Decimal("0")


@dataclass(frozen=True, slots=True)
class Insight:
    id: str
    category: str  # overall | segment | volume | consistency | composition
    severity: str  # positive | neutral | negative | warning
    title: str
    detail: str
    reliability: str | None = None


@dataclass(frozen=True, slots=True)
class SegmentStat:
    """One row of a dimension breakdown (e.g. a single buy-in bucket)."""

    key: str
    tournaments: int
    profit_base: Decimal | None
    roi_pct: Decimal | None


# A classifier maps (indicator_key, value) -> band label (or None).
Classifier = Callable[[str, Decimal | None], str | None]


def _fmt_money(v: Decimal | None) -> str:
    return f"{v:,.2f}" if v is not None else "—"


def _fmt_pct(v: Decimal | None) -> str:
    return f"{v:.1f}%" if v is not None else "—"


def build_insights(
    *,
    tournaments: int,
    roi_pct: Decimal | None,
    itm_pct: Decimal | None,
    total_profit_base: Decimal,
    total_prize_base: Decimal,
    total_bounty_base: Decimal,
    max_drawdown_base: Decimal,
    longest_loss_streak: int,
    segments: dict[str, list[SegmentStat]],
    classify: Classifier,
    reliability_label: str | None,
) -> list[Insight]:
    out: list[Insight] = []

    # --- Volume / reliability baseline -------------------------------------
    if tournaments == 0:
        return [
            Insight(
                id="no_data",
                category="volume",
                severity="neutral",
                title="Sem dados",
                detail="Cadastre torneios para gerar análises.",
            )
        ]

    low_confidence = reliability_label in {"Muito Baixa", "Baixa", None}
    out.append(
        Insight(
            id="volume",
            category="volume",
            severity="warning" if low_confidence else "neutral",
            title=f"{tournaments} torneios registrados",
            detail=(
                "Amostra pequena: trate ROI e comparações como direcionais, "
                "não conclusivos. A variância em MTT exige volume alto para "
                "validar resultados."
                if low_confidence
                else "Volume suficiente para leituras com confiança razoável."
            ),
            reliability=reliability_label,
        )
    )

    # --- Overall ROI -------------------------------------------------------
    if roi_pct is not None:
        cls = classify("roi", roi_pct)
        sev = "positive" if roi_pct > _ZERO else "negative"
        caveat = (
            " Confiabilidade baixa — não interprete como edge comprovado."
            if low_confidence
            else ""
        )
        out.append(
            Insight(
                id="overall_roi",
                category="overall",
                severity=sev,
                title=f"ROI geral: {_fmt_pct(roi_pct)}"
                + (f" ({cls})" if cls else ""),
                detail=f"Lucro acumulado de {_fmt_money(total_profit_base)}."
                + caveat,
                reliability=reliability_label,
            )
        )

    # --- ITM% --------------------------------------------------------------
    if itm_pct is not None:
        cls = classify("itm", itm_pct)
        out.append(
            Insight(
                id="overall_itm",
                category="overall",
                severity="neutral",
                title=f"ITM: {_fmt_pct(itm_pct)}" + (f" ({cls})" if cls else ""),
                detail="Percentual de torneios premiados por posição "
                "(não inclui bounties).",
                reliability=reliability_label,
            )
        )

    # --- Bounty composition (we track bounty separately) -------------------
    gross = total_prize_base + total_bounty_base
    if total_bounty_base > _ZERO and gross > _ZERO:
        share = total_bounty_base / gross * Decimal("100")
        out.append(
            Insight(
                id="bounty_share",
                category="composition",
                severity="neutral",
                title=f"Bounties = {_fmt_pct(share)} dos ganhos brutos",
                detail=f"{_fmt_money(total_bounty_base)} vieram de eliminações, "
                f"{_fmt_money(total_prize_base)} de prêmio por posição.",
            )
        )

    # --- Best / worst segment by ROI (gated) -------------------------------
    for dim, rows in segments.items():
        eligible = [
            r
            for r in rows
            if r.tournaments >= MIN_SEGMENT_N and r.roi_pct is not None
        ]
        label = _DIM_LABELS.get(dim, dim)
        if len(eligible) < 2:
            # not enough comparable segments to claim a best/worst
            if rows:
                out.append(
                    Insight(
                        id=f"segment_{dim}_insufficient",
                        category="segment",
                        severity="warning",
                        title=f"{label}: volume insuficiente para comparar",
                        detail=f"Nenhuma categoria atinge {MIN_SEGMENT_N} "
                        "torneios; ROI por categoria seria ruído.",
                    )
                )
            continue

        best = max(eligible, key=lambda r: r.roi_pct)  # type: ignore[arg-type,return-value]
        worst = min(eligible, key=lambda r: r.roi_pct)  # type: ignore[arg-type,return-value]
        out.append(
            Insight(
                id=f"segment_{dim}_best",
                category="segment",
                severity="positive",
                title=f"Melhor {label}: {best.key} ({_fmt_pct(best.roi_pct)})",
                detail=f"ROI mais alto entre suas categorias de {label} "
                f"(n={best.tournaments}).",
            )
        )
        if worst.key != best.key and worst.roi_pct is not None and worst.roi_pct < _ZERO:
            out.append(
                Insight(
                    id=f"segment_{dim}_worst",
                    category="segment",
                    severity="negative",
                    title=f"Possível vazamento em {label}: {worst.key} "
                    f"({_fmt_pct(worst.roi_pct)})",
                    detail=f"ROI negativo e mais baixo entre {label} "
                    f"(n={worst.tournaments}). Revise ou reduza volume aqui.",
                )
            )

    # --- Consistency -------------------------------------------------------
    if max_drawdown_base > _ZERO:
        out.append(
            Insight(
                id="drawdown",
                category="consistency",
                severity="neutral",
                title=f"Maior drawdown: {_fmt_money(max_drawdown_base)}",
                detail=f"Maior sequência de perdas: {longest_loss_streak} "
                "torneios. Dimensione a banca para suportar oscilações desta "
                "ordem.",
            )
        )

    return out


_DIM_LABELS = {
    "tournament_type": "tipo de torneio",
    "buy_in": "buy-in",
    "room": "sala",
    "speed": "velocidade",
    "bounty_type": "tipo de bounty",
}
