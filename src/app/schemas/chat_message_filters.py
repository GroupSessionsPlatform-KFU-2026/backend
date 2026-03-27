from uuid import UUID

from src.app.schemas.base import CommonListFilters


class ChatMessageFilters(CommonListFilters):
    sender_id: UUID | None = None
