from uuid import UUID
from src.app.schemas.base import CommonListFilters

class BoardElementFilters(CommonListFilters):
    room_id: UUID | None = None
    author_id: UUID | None = None
    element_type: str | None = None
    is_deleted: bool | None = None