from src.app.schemas.base import CommonListFilters


class PomodoroSessionFilter(CommonListFilters):
    is_running: bool | None = None
