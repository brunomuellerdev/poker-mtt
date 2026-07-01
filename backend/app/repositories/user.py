import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def exists_email(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email)
        return self.db.scalar(stmt) is not None

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()  # assign PK without committing the surrounding unit of work
        return user
