from enum import Enum
from uuid import UUID

from src.app.schemas.base import CommonListFilters


class BoardElementType(str, Enum):
    BRUSH = 'brush'
    ERASER = 'eraser'
    MARKER = 'marker'
    SHAPE = 'shape'
    TEXT = 'text'


class BoardElementFilters(CommonListFilters):
    author_id: UUID | None = None
    element_type: BoardElementType | None = None
    is_deleted: bool | None = None
