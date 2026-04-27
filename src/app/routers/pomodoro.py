from uuid import UUID

from fastapi import APIRouter, Security

from src.app.core.responses import auth_responses, detail_responses
from src.app.dependencies.room_access import require_pomodoro_moderation_access
from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import PomodoroSessionServiceDep
from src.app.models.pomodoro_session import (
    PomodoroSessionPublic,
    PomodoroSessionUpdate,
)
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/rooms/{room_id}/pomodoro',
    tags=['pomodoro'],
)


@router.get(
    '/',
    dependencies=[Security(require_scoped_user, scopes=['pomodoro:read'])],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def get_room_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> PomodoroSessionPublic:
    pomodoro = await pomodoro_service.get_room_pomodoro(room_id)

    if pomodoro is None:
        raise NotFoundError

    return pomodoro


@router.patch(
    '/settings',
    dependencies=[
        Security(
            require_pomodoro_moderation_access,
            scopes=['pomodoro:write'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def update_pomodoro_settings(
    room_id: UUID,
    pomodoro_update: PomodoroSessionUpdate,
    pomodoro_service: PomodoroSessionServiceDep,
) -> PomodoroSessionPublic:
    pomodoro = await pomodoro_service.update_room_pomodoro(room_id, pomodoro_update)

    if pomodoro is None:
        raise NotFoundError

    return pomodoro


@router.post(
    '/start',
    dependencies=[
        Security(
            require_pomodoro_moderation_access,
            scopes=['pomodoro:write'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def start_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> PomodoroSessionPublic:
    pomodoro = await pomodoro_service.start_pomodoro(room_id)

    if pomodoro is None:
        raise NotFoundError

    return pomodoro


@router.post(
    '/pause',
    dependencies=[
        Security(
            require_pomodoro_moderation_access,
            scopes=['pomodoro:write'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def pause_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> PomodoroSessionPublic:
    pomodoro = await pomodoro_service.pause_pomodoro(room_id)

    if pomodoro is None:
        raise NotFoundError

    return pomodoro


@router.post(
    '/reset',
    dependencies=[
        Security(
            require_pomodoro_moderation_access,
            scopes=['pomodoro:write'],
        )
    ],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def reset_pomodoro(
    room_id: UUID,
    pomodoro_service: PomodoroSessionServiceDep,
) -> PomodoroSessionPublic:
    pomodoro = await pomodoro_service.reset_pomodoro(room_id)

    if pomodoro is None:
        raise NotFoundError

    return pomodoro
