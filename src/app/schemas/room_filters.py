from .base import CommonListFilters


class RoomFilters(CommonListFilters):
    project_id: int | None = None
    creator_id: int | None = None
    status: str | None = None
    room_code: str | None = None
