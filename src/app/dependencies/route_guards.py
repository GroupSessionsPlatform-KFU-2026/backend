from typing import Annotated

from fastapi import Depends, Security

from src.app.dependencies.security import get_current_user
from src.app.models.user import User as UserModel


async def require_board_read(
    _: Annotated[UserModel, Security(get_current_user, scopes=['board:read'])],
) -> None:
    return None


async def require_projects_read(
    _: Annotated[UserModel, Security(get_current_user, scopes=['projects:read'])],
) -> None:
    return None


async def require_projects_write(
    _: Annotated[UserModel, Security(get_current_user, scopes=['projects:write'])],
) -> None:
    return None


async def require_projects_delete(
    _: Annotated[UserModel, Security(get_current_user, scopes=['projects:delete'])],
) -> None:
    return None


async def require_tags_read(
    _: Annotated[UserModel, Security(get_current_user, scopes=['tags:read'])],
) -> None:
    return None


async def require_tags_write(
    _: Annotated[UserModel, Security(get_current_user, scopes=['tags:write'])],
) -> None:
    return None


async def require_tags_delete(
    _: Annotated[UserModel, Security(get_current_user, scopes=['tags:delete'])],
) -> None:
    return None


async def require_rooms_read(
    _: Annotated[UserModel, Security(get_current_user, scopes=['rooms:read'])],
) -> None:
    return None


async def require_participants_read(
    _: Annotated[UserModel, Security(get_current_user, scopes=['participants:read'])],
) -> None:
    return None


async def require_pomodoro_read(
    _: Annotated[UserModel, Security(get_current_user, scopes=['pomodoro:read'])],
) -> None:
    return None


async def require_chat_read(
    _: Annotated[UserModel, Security(get_current_user, scopes=['chat:read'])],
) -> None:
    return None


CurrentRoomWriteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['rooms:write']),
]

CurrentRoomDeleteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['rooms:delete']),
]

CurrentChatWriteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['chat:write']),
]

CurrentChatDeleteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['chat:delete']),
]

CurrentParticipantWriteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['participants:write']),
]

CurrentParticipantDeleteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['participants:delete']),
]

CurrentPomodoroWriteUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['pomodoro:write']),
]

CurrentUserBoardReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['board:read']),
]

CurrentUserBoardWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['board:write']),
]

CurrentUserBoardDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['board:delete']),
]


ProjectsReadGuard = Depends(require_projects_read)
ProjectsWriteGuard = Depends(require_projects_write)
ProjectsDeleteGuard = Depends(require_projects_delete)

TagsReadGuard = Depends(require_tags_read)
TagsWriteGuard = Depends(require_tags_write)
TagsDeleteGuard = Depends(require_tags_delete)

RoomsReadGuard = Depends(require_rooms_read)
ParticipantsReadGuard = Depends(require_participants_read)
PomodoroReadGuard = Depends(require_pomodoro_read)
ChatReadGuard = Depends(require_chat_read)

BoardReadGuard = Depends(require_board_read)
