from uuid import UUID

from src.app.schemas.base import CommonListFilters


class BoardElementCommentFilters(CommonListFilters):
    author_id: UUID | None = None
    is_deleted: bool | None = None
