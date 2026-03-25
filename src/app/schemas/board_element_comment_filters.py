from uuid import UUID
from src.app.schemas.base import CommonListFilters

class BoardElementCommentFilters(CommonListFilters):
    board_element_id: UUID | None = None
    author_id: UUID | None = None
    is_deleted: bool | None = None