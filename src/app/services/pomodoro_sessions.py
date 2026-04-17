from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    PomodoroSessionRepository,
    PomodoroSessionRepositoryDep,
)
from src.app.models.pomodoro_session import (
    PomodoroPhase,
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
            current_phase=PomodoroPhase.WORK,
            completed_cycles=0,
            is_running=False,
            phase_ends_at=None,
            session_ends_at=None,
        )
        return await self.__repository.save(pomodoro)

    async def get_pomodoro(
        self,
        pomodoro_id: UUID,
    ) -> Optional[PomodoroSession]:
        return await self.__repository.get(pomodoro_id)

    async def get_room_pomodoro(
        self,
        room_id: UUID,
    ) -> Optional[PomodoroSession]:
        return await self.__repository.get_one_by_filters(
            extra_filters={'room_id': room_id},
        )

    async def update_pomodoro(
        self,
        pomodoro_update: PomodoroSessionUpdate,
        pomodoro_id: UUID,
    ) -> Optional[PomodoroSession]:
        return await self.__repository.update(pomodoro_id, pomodoro_update)

    async def update_room_pomodoro(
        self,
        room_id: UUID,
        pomodoro_update: PomodoroSessionUpdate,
    ) -> Optional[PomodoroSession]:
        session = await self.get_room_pomodoro(room_id)
        if session is None:
            return None
        return await self.__repository.update(session.id, pomodoro_update)

    async def start_pomodoro(
        self,
        room_id: UUID,
    ) -> Optional[PomodoroSession]:
        session = await self.get_room_pomodoro(room_id)
        if session is None:
            return None

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if session.current_phase == PomodoroPhase.SHORT_BREAK:
            duration = session.short_break_duration
        elif session.current_phase == PomodoroPhase.LONG_BREAK:
            duration = session.long_break_duration
        else:
            session.current_phase = PomodoroPhase.WORK
            duration = session.work_duration

        session.is_running = True
        session.phase_ends_at = now + timedelta(minutes=duration)
        return await self.__repository.save(session)

    async def pause_pomodoro(
        self,
        room_id: UUID,
    ) -> Optional[PomodoroSession]:
        session = await self.get_room_pomodoro(room_id)
        if session is None:
            return None

        session.is_running = False
        return await self.__repository.save(session)

    async def reset_pomodoro(
        self,
        room_id: UUID,
    ) -> Optional[PomodoroSession]:
        session = await self.get_room_pomodoro(room_id)
        if session is None:
            return None

        session.completed_cycles = 0
        session.current_phase = PomodoroPhase.WORK
        session.is_running = False
        session.phase_ends_at = None
        session.session_ends_at = None
        return await self.__repository.save(session)
