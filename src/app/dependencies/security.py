from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from src.app.core.security import oauth2_scheme
from src.app.dependencies.services import AuthServiceDep
from src.app.models.user import User as UserModel

type AuthenticatedUser = UserModel | None


async def authenticate_user(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
) -> AuthenticatedUser:
    return await auth_service.authenticate_user(
        email=auth_data.username,
        password=auth_data.password,
    )


AuthenticatedUserDep = Annotated[AuthenticatedUser, Depends(authenticate_user)]


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDep,
) -> UserModel:
    return await auth_service.get_current_user(
        token=token,
        required_scopes=security_scopes.scopes,
    )


CurrentUserUsersWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['users:write']),
]

CurrentProfileUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['profile:read']),
]

CurrentUsersReadUserDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['users:read']),
]

CurrentUserTagsReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['tags:read']),
]

CurrentUserTagsWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['tags:write']),
]

CurrentUserTagsDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['tags:delete']),
]

CurrentUserProfileReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['profile:read']),
]
CurrentUserProfileWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['profile:write']),
]

CurrentUserProjectsReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['projects:read']),
]
CurrentUserProjectsWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['projects:write']),
]
CurrentUserProjectsDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['projects:delete']),
]

CurrentUserRoomsReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['rooms:read']),
]
CurrentUserRoomsWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['rooms:write']),
]
CurrentUserRoomsDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['rooms:delete']),
]

CurrentUserParticipantsReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['participants:read']),
]
CurrentUserParticipantsWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['participants:write']),
]
CurrentUserParticipantsDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['participants:delete']),
]

CurrentUserChatReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['chat:read']),
]
CurrentUserChatWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['chat:write']),
]
CurrentUserChatDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['chat:delete']),
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

CurrentUserPomodoroReadDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['pomodoro:read']),
]
CurrentUserPomodoroWriteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['pomodoro:write']),
]
CurrentUserPomodoroDeleteDep = Annotated[
    UserModel,
    Security(get_current_user, scopes=['pomodoro:delete']),
]