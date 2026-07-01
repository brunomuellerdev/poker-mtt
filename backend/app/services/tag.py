import uuid

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError
from app.db.models import Tag


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class TagAlreadyExists(DomainError):
    pass


class TagNotFound(DomainError):
    pass


class TagService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, user_id: uuid.UUID) -> list[Tag]:
        stmt = select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)
        return list(self.db.scalars(stmt))

    def create(self, user_id: uuid.UUID, data: TagCreate) -> Tag:
        tag = Tag(user_id=user_id, name=data.name)
        self.db.add(tag)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise TagAlreadyExists(data.name) from exc
        self.db.refresh(tag)
        return tag

    def delete(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        tag = self.db.scalar(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        )
        if tag is None:
            raise TagNotFound(str(tag_id))
        self.db.delete(tag)
        self.db.commit()
