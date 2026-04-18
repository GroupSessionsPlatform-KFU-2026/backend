from typing import Optional
from uuid import UUID

from fastapi import APIRouter

from src.app.dependencies.route_guards import (
    CurrentPomodoroWriteUserDep,
    PomodoroReadGuard,
)
from src.app.dependencies.services import (
    PomodoroSessionServiceDep,
    RoomAccessServiceDep,
)
from src.app.models.pomodoro_session import (
    PomodoroSessionPublic,
    PomodoroSessionUpdate,
)

router = APIRouter(
    prefix='/rooms/{room_id}/pomodoro',
    tags=['pomodoro'],
)


@router.get('/', dependencies=[PomodoroReadGuard])
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
    current_user: CurrentPomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.update_room_pomodoro(room_id, pomodoro_update)


@router.post('/start')
async def start_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: CurrentPomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.start_pomodoro(room_id)


@router.post('/pause')
async def pause_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: CurrentPomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.pause_pomodoro(room_id)


@router.post('/reset')
async def reset_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
    room_access: RoomAccessServiceDep,
    current_user: CurrentPomodoroWriteUserDep,
) -> Optional[PomodoroSessionPublic]:
    await room_access.ensure_can_moderate(room_id, current_user.id)
    return await pomodoro_service.reset_pomodoro(room_id)
