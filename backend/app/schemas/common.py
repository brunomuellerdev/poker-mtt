from pydantic import BaseModel


class PageOut[T](BaseModel):
    items: list[T]
    next_offset: int | None = None
    has_more: bool = False
