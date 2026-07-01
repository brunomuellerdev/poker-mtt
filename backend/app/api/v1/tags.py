import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.services.tag import (
    TagAlreadyExists,
    TagCreate,
    TagNotFound,
    TagOut,
    TagService,
)

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
def list_tags(current_user: CurrentUser, db: DbSession) -> list[TagOut]:
    tags = TagService(db).list(current_user.id)
    return [TagOut.model_validate(t) for t in tags]


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(data: TagCreate, current_user: CurrentUser, db: DbSession) -> TagOut:
    try:
        tag = TagService(db).create(current_user.id, data)
    except TagAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tag already exists"
        ) from exc
    return TagOut.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    try:
        TagService(db).delete(current_user.id, tag_id)
    except TagNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        ) from exc
