import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.db.models import MarkedHand
from app.schemas.marked_hand import (
    MarkedHandCreate,
    MarkedHandOut,
    MarkedHandReplayOut,
    MarkedHandUpdate,
)

router = APIRouter(prefix="/marked-hands", tags=["marked-hands"])


def _get(db, user_id: uuid.UUID, hand_id: uuid.UUID) -> MarkedHand:
    hand = db.scalar(
        select(MarkedHand).where(
            MarkedHand.id == hand_id, MarkedHand.user_id == user_id
        )
    )
    if hand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Marked hand not found"
        )
    return hand


def _to_out(h: MarkedHand) -> MarkedHandOut:
    return MarkedHandOut(
        id=h.id,
        hand_code=h.hand_code,
        poker_room=h.poker_room,
        date=h.date,
        hero_cards=h.hero_cards,
        board=h.board,
        has_replay=h.replay is not None,
    )


@router.get("", response_model=list[MarkedHandOut])
def list_marked_hands(
    current_user: CurrentUser, db: DbSession
) -> list[MarkedHandOut]:
    stmt = (
        select(MarkedHand)
        .where(MarkedHand.user_id == current_user.id)
        .order_by(MarkedHand.date.desc(), MarkedHand.created_at.desc())
    )
    return [_to_out(h) for h in db.scalars(stmt)]


@router.post(
    "", response_model=MarkedHandOut, status_code=status.HTTP_201_CREATED
)
def create_marked_hand(
    data: MarkedHandCreate, current_user: CurrentUser, db: DbSession
) -> MarkedHandOut:
    replay = data.replay
    hero_cards = replay.get("hero_cards") if replay else None
    board = replay.get("board") if replay else None
    hand = MarkedHand(
        user_id=current_user.id,
        hand_code=data.hand_code,
        poker_room=data.poker_room,
        date=data.date,
        replay=replay,
        hero_cards=hero_cards,
        board=board,
    )
    db.add(hand)
    db.commit()
    db.refresh(hand)
    return _to_out(hand)


@router.get("/{hand_id}/replay", response_model=MarkedHandReplayOut)
def get_marked_hand_replay(
    hand_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> MarkedHandReplayOut:
    hand = _get(db, current_user.id, hand_id)
    return MarkedHandReplayOut(
        id=hand.id, hand_code=hand.hand_code, replay=hand.replay
    )


@router.patch("/{hand_id}", response_model=MarkedHandOut)
def update_marked_hand(
    hand_id: uuid.UUID,
    data: MarkedHandUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> MarkedHandOut:
    hand = _get(db, current_user.id, hand_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(hand, field, value)
    db.commit()
    db.refresh(hand)
    return _to_out(hand)


@router.delete("/{hand_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marked_hand(
    hand_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> None:
    hand = _get(db, current_user.id, hand_id)
    db.delete(hand)
    db.commit()
