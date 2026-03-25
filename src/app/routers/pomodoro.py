from typing import Optional
from uuid import UUID

from fastapi import APIRouter

from src.app.dependencies.services import PomodoroSessionServiceDep
from src.app.models.pomodoro_session import (
    PomodoroSessionPublic,
    PomodoroSessionUpdate,
)

router = APIRouter(
    prefix='/rooms/{room_id}/pomodoro',
    tags=['pomodoro'],
)


@router.get('/')
async def get_room_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> Optional[PomodoroSessionPublic]:
    return await pomodoro_service.get_room_pomodoro(room_id)


@router.patch('/settings')
async def update_pomodoro_settings(
    room_id: UUID,
    pomodoro_update: PomodoroSessionUpdate,
    pomodoro_service: PomodoroSessionServiceDep,
) -> Optional[PomodoroSessionPublic]:
    session = await pomodoro_service.get_room_pomodoro(room_id)
    if session is None:
        return None
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.update_pomodoro(pomodoro_update, session.id)


@router.post('/start')
async def start_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> Optional[PomodoroSessionPublic]:
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.start_pomodoro(room_id)


@router.post('/pause')
async def pause_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> Optional[PomodoroSessionPublic]:
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.pause_pomodoro(room_id)


@router.post('/reset')
async def reset_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> Optional[PomodoroSessionPublic]:
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.reset_pomodoro(room_id)
