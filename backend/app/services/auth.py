from sqlalchemy.orm import Session

from app.core.defaults import DEFAULT_EVALUATION_RANGES
from app.core.exceptions import EmailAlreadyExists, InvalidCredentials
from app.core.security import (
    hash_password,
    needs_rehash,
    verify_password,
)
from app.db.models import EvaluationRange, User, UserSettings
from app.repositories.user import UserRepository
from app.schemas.auth import UserRegister


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, data: UserRegister) -> User:
        # normalize email to avoid case-duplicate accounts
        email = data.email.lower()
        if self.users.exists_email(email):
            raise EmailAlreadyExists(email)

        user = User(
            name=data.name,
            email=email,
            password_hash=hash_password(data.password),
        )
        self.users.add(user)  # flush -> user.id available

        self.db.add(UserSettings(user_id=user.id))
        self._seed_evaluation_ranges(user)

        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email.lower())
        # verify even when user is None to keep timing uniform against enumeration
        reference_hash = (
            user.password_hash
            if user is not None
            else "$argon2id$v=19$m=65536,t=3,p=4$"
            "AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )
        ok = verify_password(password, reference_hash)
        if user is None or not ok:
            raise InvalidCredentials()

        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
            self.db.commit()
        return user

    def _seed_evaluation_ranges(self, user: User) -> None:
        rows = [
            EvaluationRange(
                user_id=user.id,
                indicator_key=key,
                range_order=order,
                lower_bound=lower,
                upper_bound=upper,
                label=label,
            )
            for key, bands in DEFAULT_EVALUATION_RANGES.items()
            for order, (lower, upper, label) in enumerate(bands)
        ]
        self.db.add_all(rows)
