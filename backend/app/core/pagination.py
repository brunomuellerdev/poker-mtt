"""Offset pagination.

For a single-user tracker (thousands of rows at most) offset/limit is simple,
supports arbitrary ORDER BY (including nullable columns and multi-key sorts),
and has no meaningful downside at this scale.
"""


class Page[T]:
    def __init__(self, items: list[T], has_more: bool, next_offset: int | None):
        self.items = items
        self.has_more = has_more
        self.next_offset = next_offset
