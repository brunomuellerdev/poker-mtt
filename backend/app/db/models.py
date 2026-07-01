import uuid
from datetime import date, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.db.enums import (
    BettingStructure,
    BountyType,
    GameType,
    Speed,
    TournamentStatus,
    TournamentType,
)


def _pg_enum(enum_cls: type, name: str, length: int):
    """VARCHAR + CHECK using enum VALUES (not member names) for storage and validation."""
    return Enum(
        enum_cls,
        native_enum=False,
        length=length,
        create_constraint=True,
        name=name,
        values_callable=lambda e: [m.value for m in e],
    )


# Cost expression reused across generated columns (PG forbids GENERATED -> GENERATED)
_COST_EXPR = "buy_in * (1 + rebuys + reentries) + addon_cost"
# Total winnings = position prize + bounty. COALESCE so 'registered' rows
# (prize/bounty NULL) yield 0 instead of NULL (generated cols are NOT NULL).
_WINNINGS_EXPR = "COALESCE(prize, 0) + COALESCE(bounty, 0)"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    tournaments: Mapped[list["Tournament"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSettings(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    base_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default=text("'USD'")
    )
    theme: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dark", server_default=text("'dark'")
    )
    default_table_size: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=9, server_default=text("9")
    )

    user: Mapped["User"] = relationship(back_populates="settings")



class Tournament(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tournaments"
    __table_args__ = (
        Index("ix_tournaments_order", "user_id", "date", "start_time", "id"),
        Index("ix_tournaments_user_room", "user_id", "poker_room"),
        Index("ix_tournaments_user_profit", "user_id", "profit_base"),
        CheckConstraint("buy_in >= 0", name="ck_tour_buyin_nonneg"),
        CheckConstraint("prize >= 0", name="ck_tour_prize_nonneg"),
        CheckConstraint(
            "rebuys >= 0 AND reentries >= 0 AND add_ons >= 0",
            name="ck_tour_counts_nonneg",
        ),
        CheckConstraint("final_position >= 1", name="ck_tour_position"),
        CheckConstraint("entrants >= 1", name="ck_tour_entrants"),
        CheckConstraint("fx_rate_to_base > 0", name="ck_tour_fx_positive"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    poker_room: Mapped[str] = mapped_column(String(100), nullable=False)
    tournament_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    game_type: Mapped[GameType] = mapped_column(
        _pg_enum(GameType, "ck_tour_game_type", 20), nullable=False
    )
    betting_structure: Mapped[BettingStructure] = mapped_column(
        _pg_enum(BettingStructure, "ck_tour_betting_structure", 4), nullable=False
    )
    speed: Mapped[Speed] = mapped_column(
        _pg_enum(Speed, "ck_tour_speed", 10),
        nullable=False,
        default=Speed.REGULAR,
        server_default=text("'regular'"),
    )
    tournament_type: Mapped[TournamentType] = mapped_column(
        _pg_enum(TournamentType, "ck_tour_tournament_type", 12),
        nullable=False,
        default=TournamentType.NORMAL,
        server_default=text("'normal'"),
    )
    # chip-purchase policy — independent flags (combine freely);
    # freezeout = all three false
    allows_rebuy: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    allows_reentry: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    allows_addon: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    bounty_type: Mapped[BountyType] = mapped_column(
        _pg_enum(BountyType, "ck_tour_bounty_type", 12),
        nullable=False,
        default=BountyType.NONE,
        server_default=text("'none'"),
    )

    table_size: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=9, server_default=text("9")
    )
    final_table_size: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=9, server_default=text("9")
    )

    # currency (default 1.0; storage always native)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default=text("'USD'")
    )
    fx_rate_to_base: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        default=Decimal("1.0"),
        server_default=text("1.0"),
    )

    # native values
    buy_in: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    addon_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0"), server_default=text("0")
    )
    guarantee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    # nullable: empty while only 'registered'; a completed tournament sets these
    prize: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True, default=Decimal("0"), server_default=text("0")
    )
    # bounty/knockout winnings — earned per elimination, independent of ITM
    bounty: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True, default=Decimal("0"), server_default=text("0")
    )

    rebuys: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default=text("0")
    )
    reentries: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default=text("0")
    )
    add_ons: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default=text("0")
    )

    entrants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 'registered' = only signed up, no result yet (excluded from all metrics);
    # 'completed' = has a result and counts in metrics
    status: Mapped[TournamentStatus] = mapped_column(
        _pg_enum(TournamentStatus, "ck_tour_status", 12),
        nullable=False,
        server_default=TournamentStatus.COMPLETED.value,
    )

    # generated columns (expressions inlined; see _COST_EXPR / _WINNINGS_EXPR)
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), Computed(_COST_EXPR, persisted=True)
    )
    total_winnings: Mapped[Decimal] = mapped_column(
        Numeric(16, 2), Computed(_WINNINGS_EXPR, persisted=True)
    )
    profit_native: Mapped[Decimal] = mapped_column(
        Numeric(16, 2),
        Computed(f"({_WINNINGS_EXPR}) - ({_COST_EXPR})", persisted=True),
    )
    profit_base: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        Computed(
            f"(({_WINNINGS_EXPR}) - ({_COST_EXPR})) * fx_rate_to_base",
            persisted=True,
        ),
    )
    # ITM is determined by the POSITION prize only, not bounty winnings.
    # COALESCE so 'registered' rows (prize/final_position NULL) yield false.
    itm: Mapped[bool] = mapped_column(Computed("COALESCE(prize > 0, false)", persisted=True))
    winner: Mapped[bool] = mapped_column(
        Computed("COALESCE(final_position = 1, false)", persisted=True)
    )
    final_table: Mapped[bool] = mapped_column(
        Computed(
            "COALESCE(final_position <= final_table_size, false)", persisted=True
        )
    )

    user: Mapped["User"] = relationship(back_populates="tournaments")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="tournament_tags", back_populates="tournaments"
    )


class Tag(UUIDMixin, Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    tournaments: Mapped[list["Tournament"]] = relationship(
        secondary="tournament_tags", back_populates="tags"
    )


class TournamentTag(Base):
    __tablename__ = "tournament_tags"

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )



class EvaluationRange(UUIDMixin, Base):
    """Generic classification bands, per user, per indicator.
    Half-open interval [lower, upper): NULL = -inf / +inf."""

    __tablename__ = "evaluation_ranges"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "indicator_key",
            "range_order",
            name="uq_eval_user_indicator_order",
        ),
        Index("ix_eval_user_indicator", "user_id", "indicator_key"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    indicator_key: Mapped[str] = mapped_column(String(40), nullable=False)
    range_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    lower_bound: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    upper_bound: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4), nullable=True
    )
    label: Mapped[str] = mapped_column(String(40), nullable=False)


class MarkedHand(UUIDMixin, TimestampMixin, Base):
    """A hand the user flags to study later: just an identifier, room and date."""

    __tablename__ = "marked_hands"
    __table_args__ = (Index("ix_marked_hands_user_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    hand_code: Mapped[str] = mapped_column(String(100), nullable=False)
    poker_room: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    # replay payload (full parsed hand dict) — present when marked from the
    # replayer; null for hands entered manually on the Marked Hands page
    replay: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    hero_cards: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    board: Mapped[list | None] = mapped_column(JSONB, nullable=True)
