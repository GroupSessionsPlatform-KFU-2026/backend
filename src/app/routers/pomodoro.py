from typing import Optional, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from fastapi import Security
from src.app.dependencies.security import get_current_user
from src.app.models.user import User
from src.app.services.pomodoro_sessions import PomodoroSessionService
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
    pomodoro_service: PomodoroSessionService = Depends(),
    current_user: User = Security(get_current_user, scopes=['pomodoro:read']),
) -> Optional[PomodoroSessionPublic]:
    return await pomodoro_service.get_room_pomodoro(room_id)


@router.patch('/settings')
async def update_pomodoro_settings(
    room_id: UUID,
    pomodoro_update: PomodoroSessionUpdate,
    pomodoro_service: PomodoroSessionService = Depends(),
    current_user: User = Security(get_current_user, scopes=['pomodoro:write']),
) -> Optional[PomodoroSessionPublic]:
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.update_room_pomodoro(room_id, pomodoro_update)


@router.post('/start')
async def start_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionService = Depends(),
    current_user: User = Security(get_current_user, scopes=['pomodoro:write']),
) -> Optional[PomodoroSessionPublic]:
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.start_pomodoro(room_id)


@router.post('/pause')
async def pause_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionService = Depends(),
    current_user: User = Security(get_current_user, scopes=['pomodoro:write']),
) -> Optional[PomodoroSessionPublic]:
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.pause_pomodoro(room_id)


@router.post('/reset')
async def reset_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionService = Depends(),
    current_user: User = Security(get_current_user, scopes=['pomodoro:write']),
) -> Optional[PomodoroSessionPublic]:
    # TODO: validate room ownership/moderation after auth is implemented.
    return await pomodoro_service.reset_pomodoro(room_id)
