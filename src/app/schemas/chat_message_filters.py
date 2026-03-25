from uuid import UUID
from src.app.schemas.base import CommonListFilters

class ChatMessageFilters(CommonListFilters):
    room_id: UUID | None = None
    sender_id: UUID | None = None