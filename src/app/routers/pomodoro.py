from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Security

from src.app.dependencies.security import get_current_user
from src.app.dependencies.services import (
    PomodoroSessionServiceDep,
    RoomAccessServiceDep,
)
from src.app.models.pomodoro_session import (
    PomodoroSessionPublic,
    PomodoroSessionUpdate,
)
from src.app.models.user import User as UserModel

router = APIRouter(
    prefix='/rooms/{room_id}/pomodoro',
    tags=['pomodoro'],
)

PomodoroWriteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['pomodoro:write']),
]


@router.get('/', dependencies=[Security(get_current_user, scopes=['pomodoro:read'])])
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
    room_access: RoomAccessServiceDep,
    current_user: PomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.update_room_pomodoro(room_id, pomodoro_update)


@router.post('/start')
async def start_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: PomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.start_pomodoro(room_id)


@router.post('/pause')
async def pause_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: PomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.pause_pomodoro(room_id)


@router.post('/reset')
async def reset_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: PomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.reset_pomodoro(room_id)
