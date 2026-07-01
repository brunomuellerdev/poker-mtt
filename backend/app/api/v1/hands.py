from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import CurrentUser
from app.core.hands import hand_to_dict, parse_hands

router = APIRouter(prefix="/hands", tags=["hands"])

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB guard


@router.post("/parse")
async def parse_hand_file(file: UploadFile, current_user: CurrentUser) -> dict:
    """Parse an uploaded PokerStars NLHE hand-history file into replay frames.
    Stateless — nothing is persisted."""
    raw = await file.read()
    if len(raw) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    try:
        hands = parse_hands(text)
    except Exception as exc:  # noqa: BLE001 - surface a clean parse error
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse hand history: {exc}",
        ) from exc

    if not hands:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No PokerStars hands found in file",
        )
    return {"hands": [hand_to_dict(h) for h in hands]}
