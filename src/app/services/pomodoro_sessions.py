from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from src.app.dependencies.repositories import (
    PomodoroRepository,
    PomodoroRepositoryDep,
)
from src.app.models.pomodoro_session import PomodoroSession


class PomodoroService:
    __repository: PomodoroRepository

    def __init__(self, repository: PomodoroRepositoryDep):
        self.__repository = repository

    async def get_pomodoro(self, room_id: UUID) -> Optional[PomodoroSession]:
        return await self.__repository.get_by_room(room_id)

    async def start(self, room_id: UUID) -> Optional[PomodoroSession]:
        session = await self.__repository.get_by_room(room_id)
        if not session:
            return None

        session.is_running = True
        session.phase_ends_at = datetime.utcnow() + timedelta(
            minutes=session.work_duration
        )

        return await self.__repository.save(session)

    async def pause(self, room_id: UUID) -> Optional[PomodoroSession]:
        session = await self.__repository.get_by_room(room_id)
        if not session:
            return None

        session.is_running = False
        return await self.__repository.save(session)

    async def reset(self, room_id: UUID) -> Optional[PomodoroSession]:
        session = await self.__repository.get_by_room(room_id)
        if not session:
            return None

        session.completed_cycles = 0
        session.is_running = False

        return await self.__repository.save(session)