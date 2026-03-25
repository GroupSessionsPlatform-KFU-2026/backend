from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    PomodoroSessionRepository,
    PomodoroSessionRepositoryDep,
)
from src.app.models.pomodoro_session import (
    PomodoroSession,
    PomodoroSessionCreate,
    PomodoroSessionUpdate,
)
from src.app.schemas.pomodoro_session_filters import PomodoroSessionFilter


class PomodoroSessionService:
    __repository: PomodoroSessionRepository

    def __init__(self, repository: PomodoroSessionRepositoryDep):
        self.__repository = repository

    async def get_pomodoros(
        self,
        filters: PomodoroSessionFilter,
    ) -> Sequence[PomodoroSession]:
        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_pomodoro(
        self,
        pomodoro_create: PomodoroSessionCreate,
    ) -> PomodoroSession:
        pomodoro_dump = pomodoro_create.model_dump()
        pomodoro = PomodoroSession(
            **pomodoro_dump,
            current_phase='work',
            completed_cycles=0,
            is_running=False,
            phase_ends_at=None,
            session_ends_at=None,
            last_updated_at=datetime.now(timezone.utc),
        )
        return await self.__repository.save(pomodoro)

    async def get_pomodoro(self, pomodoro_id: UUID) -> Optional[PomodoroSession]:
        return await self.__repository.get(pomodoro_id)

    async def get_room_pomodoro(self, room_id: UUID) -> Optional[PomodoroSession]:
        filters = PomodoroSessionFilter(room_id=room_id, offset=0, limit=1)
        sessions = await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )
        return sessions[0] if sessions else None

    async def update_pomodoro(
        self,
        pomodoro_update: PomodoroSessionUpdate,
        pomodoro_id: UUID,
    ) -> Optional[PomodoroSession]:
        update_data = pomodoro_update.model_dump(exclude_unset=True)
        update_data['last_updated_at'] = datetime.now(timezone.utc)
        prepared_update = PomodoroSessionUpdate(**update_data)
        return await self.__repository.update(pomodoro_id, prepared_update)

    async def start_pomodoro(self, room_id: UUID) -> Optional[PomodoroSession]:
        session = await self.get_room_pomodoro(room_id)
        if session is None:
            return None

        now = datetime.now(timezone.utc)
        session.is_running = True
        session.current_phase = 'work'
        session.phase_ends_at = now + timedelta(minutes=session.work_duration)
        session.last_updated_at = now
        return await self.__repository.save(session)

    async def pause_pomodoro(self, room_id: UUID) -> Optional[PomodoroSession]:
        session = await self.get_room_pomodoro(room_id)
        if session is None:
            return None

        session.is_running = False
        session.current_phase = 'paused'
        session.last_updated_at = datetime.now(timezone.utc)
        return await self.__repository.save(session)

    async def reset_pomodoro(self, room_id: UUID) -> Optional[PomodoroSession]:
        session = await self.get_room_pomodoro(room_id)
        if session is None:
            return None

        session.completed_cycles = 0
        session.current_phase = 'work'
        session.is_running = False
        session.phase_ends_at = None
        session.session_ends_at = None
        session.last_updated_at = datetime.now(timezone.utc)
        return await self.__repository.save(session)
