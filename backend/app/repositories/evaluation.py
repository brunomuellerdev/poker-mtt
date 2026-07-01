import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.metrics.classification import Band
from app.db.models import EvaluationRange


class EvaluationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def bands(self, user_id: uuid.UUID, indicator_key: str) -> list[Band]:
        stmt = (
            select(EvaluationRange)
            .where(
                EvaluationRange.user_id == user_id,
                EvaluationRange.indicator_key == indicator_key,
            )
            .order_by(EvaluationRange.range_order)
        )
        return [
            Band(lower=r.lower_bound, upper=r.upper_bound, label=r.label)
            for r in self.db.scalars(stmt)
        ]
