import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSessionType

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import DomainError
from app.db.enums import EmotionalState
from app.db.models import Session as SessionModel


class SessionCreate(BaseModel):
    started_at: datetime
    ended_at: datetime | None = None
    average_tables: int | None = Field(default=None, ge=1)
    concentration_level: int | None = Field(default=None, ge=1, le=5)
    emotional_state: EmotionalState | None = None
    notes: str | None = None


class SessionUpdate(BaseModel):
    started_at: datetime | None = None
    ended_at: datetime | None = None
    average_tables: int | None = Field(default=None, ge=1)
    concentration_level: int | None = Field(default=None, ge=1, le=5)
    emotional_state: EmotionalState | None = None
    notes: str | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: int | None
    average_tables: int | None
    concentration_level: int | None
    emotional_state: EmotionalState | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SessionNotFound(DomainError):
    pass


class SessionService:
    def __init__(self, db: DbSessionType) -> None:
        self.db = db

    def _get(self, user_id: uuid.UUID, session_id: uuid.UUID) -> SessionModel | None:
        return self.db.scalar(
            select(SessionModel).where(
                SessionModel.id == session_id, SessionModel.user_id == user_id
            )
        )

    def list(self, user_id: uuid.UUID) -> list[SessionModel]:
        stmt = (
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .order_by(SessionModel.started_at.desc())
        )
        return list(self.db.scalars(stmt))

    def create(self, user_id: uuid.UUID, data: SessionCreate) -> SessionModel:
        s = SessionModel(user_id=user_id, **data.model_dump())
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def update(
        self, user_id: uuid.UUID, session_id: uuid.UUID, data: SessionUpdate
    ) -> SessionModel:
        s = self._get(user_id, session_id)
        if s is None:
            raise SessionNotFound(str(session_id))
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(s, k, v)
        self.db.commit()
        self.db.refresh(s)
        return s

    def delete(self, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        s = self._get(user_id, session_id)
        if s is None:
            raise SessionNotFound(str(session_id))
        self.db.delete(s)
        self.db.commit()


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
def list_sessions(current_user: CurrentUser, db: DbSession) -> list[SessionOut]:
    return [SessionOut.model_validate(s) for s in SessionService(db).list(current_user.id)]


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    data: SessionCreate, current_user: CurrentUser, db: DbSession
) -> SessionOut:
    return SessionOut.model_validate(SessionService(db).create(current_user.id, data))


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(
    session_id: uuid.UUID, data: SessionUpdate, current_user: CurrentUser, db: DbSession
) -> SessionOut:
    try:
        s = SessionService(db).update(current_user.id, session_id, data)
    except SessionNotFound as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    return SessionOut.model_validate(s)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> None:
    try:
        SessionService(db).delete(current_user.id, session_id)
    except SessionNotFound as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
