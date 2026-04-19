from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import SecurityScopes

from src.app.dependencies.security import CurrentUserDep
from src.app.dependencies.services import AuthServiceDep, RoomAccessServiceDep
from src.app.models.user import User
from src.app.services.auth import AuthService
from src.app.services.room_access import RoomAccessService


@dataclass(slots=True)
class RoomAccessContext:
    current_user: User
    auth_service: AuthService
    room_access: RoomAccessService


async def get_room_access_context(
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
    room_access: RoomAccessServiceDep,
) -> RoomAccessContext:
    return RoomAccessContext(
        current_user=current_user,
        auth_service=auth_service,
        room_access=room_access,
    )


RoomAccessContextDep = Annotated[
    RoomAccessContext,
    Depends(get_room_access_context),
]


async def require_room_moderation_access(
    security_scopes: SecurityScopes,
    room_id: UUID,
    ctx: RoomAccessContextDep,
) -> None:
    ctx.auth_service.ensure_user_scopes(
        ctx.current_user,
        security_scopes.scopes,
    )
    await ctx.room_access.ensure_can_moderate(room_id, ctx.current_user.id)


async def require_message_manage_access(
    security_scopes: SecurityScopes,
    room_id: UUID,
    message_id: UUID,
    ctx: RoomAccessContextDep,
) -> None:
    ctx.auth_service.ensure_user_scopes(
        ctx.current_user,
        security_scopes.scopes,
    )
    await ctx.room_access.ensure_message_manage(
        room_id,
        message_id,
        ctx.current_user.id,
    )


async def require_board_element_manage_access(
    security_scopes: SecurityScopes,
    room_id: UUID,
    element_id: UUID,
    ctx: RoomAccessContextDep,
) -> None:
    ctx.auth_service.ensure_user_scopes(
        ctx.current_user,
        security_scopes.scopes,
    )
    await ctx.room_access.ensure_board_element_manage(
        room_id,
        element_id,
        ctx.current_user.id,
    )


async def require_comment_manage_access(
    security_scopes: SecurityScopes,
    room_id: UUID,
    element_id: UUID,
    comment_id: UUID,
    ctx: RoomAccessContextDep,
) -> None:
    ctx.auth_service.ensure_user_scopes(
        ctx.current_user,
        security_scopes.scopes,
    )
    await ctx.room_access.ensure_comment_manage(
        room_id,
        element_id,
        comment_id,
        ctx.current_user.id,
    )


async def require_pomodoro_moderation_access(
    security_scopes: SecurityScopes,
    room_id: UUID,
    ctx: RoomAccessContextDep,
) -> None:
    ctx.auth_service.ensure_user_scopes(
        ctx.current_user,
        security_scopes.scopes,
    )
    await ctx.room_access.ensure_can_moderate(room_id, ctx.current_user.id)
