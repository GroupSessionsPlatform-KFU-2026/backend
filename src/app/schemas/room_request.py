from uuid import UUID

from pydantic import BaseModel


class JoinRoomRequest(BaseModel):
    room_code: str
    user_id: UUID
