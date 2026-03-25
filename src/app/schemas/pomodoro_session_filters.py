from uuid import UUID
from src.app.schemas.base import CommonListFilters

class PomodoroSessionFilter(CommonListFilters):
    room_id: UUID | None = None
    is_running: bool | None = None