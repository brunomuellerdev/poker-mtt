import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import DomainError
from app.db.models import Tournament
from app.repositories.tournament import TournamentRepository
from app.schemas.tournament import TournamentCreate, TournamentUpdate


class TournamentNotFound(DomainError):
    pass


class InvalidTagReference(DomainError):
    pass


class TournamentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TournamentRepository(db)

    def create(self, user_id: uuid.UUID, data: TournamentCreate) -> Tournament:
        payload = data.model_dump(exclude={"tag_ids"})
        # pending design decision: final table defaults to the table size
        if payload.get("final_table_size") is None:
            payload["final_table_size"] = payload["table_size"]

        tournament = Tournament(user_id=user_id, **payload)
        self._attach_tags(user_id, tournament, data.tag_ids)
        self.repo.add(tournament)
        self.db.commit()
        # expire so the reload reflects DB-normalized values (numeric scale,
        # generated columns) instead of the in-memory pre-commit decimals
        self.db.expire(tournament)
        return self.repo.get(user_id, tournament.id)  # type: ignore[return-value]

    def update(
        self, user_id: uuid.UUID, tournament_id: uuid.UUID, data: TournamentUpdate
    ) -> Tournament:
        tournament = self.repo.get(user_id, tournament_id)
        if tournament is None:
            raise TournamentNotFound(str(tournament_id))

        changes = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
        for key, value in changes.items():
            setattr(tournament, key, value)

        # a 'registered' tournament never carries a result, whatever was sent
        from app.db.enums import TournamentStatus

        if tournament.status == TournamentStatus.REGISTERED:
            tournament.entrants = None
            tournament.final_position = None
            tournament.prize = None
            tournament.bounty = None

        if data.tag_ids is not None:
            tournament.tags.clear()
            self._attach_tags(user_id, tournament, data.tag_ids)

        self.db.commit()
        self.db.expire(tournament)
        return self.repo.get(user_id, tournament_id)  # type: ignore[return-value]

    def delete(self, user_id: uuid.UUID, tournament_id: uuid.UUID) -> None:
        tournament = self.repo.get(user_id, tournament_id)
        if tournament is None:
            raise TournamentNotFound(str(tournament_id))
        self.repo.delete(tournament)
        self.db.commit()

    def _attach_tags(
        self, user_id: uuid.UUID, tournament: Tournament, tag_ids: list[uuid.UUID]
    ) -> None:
        if not tag_ids:
            return
        tags = self.repo.get_tags(user_id, tag_ids)
        if len(tags) != len(set(tag_ids)):
            # a referenced tag does not exist or belongs to another user
            raise InvalidTagReference()
        tournament.tags.extend(tags)
