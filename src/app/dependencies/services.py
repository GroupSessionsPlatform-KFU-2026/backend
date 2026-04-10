from typing import Annotated

from fastapi import Depends

from src.app.dependencies.repositories import (
    RefreshSessionRepositoryDep,
    RoleRepositoryDep,
    UserRepositoryDep,
    UserRoleRepositoryDep,
)
from src.app.services.auth import AuthService
from src.app.services.board_elements import BoardElementService
from src.app.services.board_elements_comments import BoardElementCommentService
from src.app.services.chat_messages import ChatMessageService
from src.app.services.pomodoro_sessions import PomodoroSessionService
from src.app.services.projects import ProjectService
from src.app.services.rbac_bootstrap import RBACBootstrapService
from src.app.services.room_participants import RoomParticipantService
from src.app.services.rooms import RoomService
from src.app.services.tags import TagService
from src.app.services.users import UserService
from src.app.services.rbac_bootstrap import RBACBootstrapService

AuthServiceDep = Annotated[AuthService, Depends(AuthService)]
UserServiceDep = Annotated[UserService, Depends(UserService)]


def get_auth_service(
    user_repository: UserRepositoryDep,
    refresh_session_repository: RefreshSessionRepositoryDep,
    role_repository: RoleRepositoryDep,
    user_role_repository: UserRoleRepositoryDep,
    user_service: UserServiceDep,
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
        refresh_session_repository=refresh_session_repository,
        role_repository=role_repository,
        user_role_repository=user_role_repository,
        user_service=user_service,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(ProjectService)]
TagServiceDep = Annotated[TagService, Depends(TagService)]
RoomServiceDep = Annotated[RoomService, Depends(RoomService)]
RoomParticipantServiceDep = Annotated[
    RoomParticipantService, Depends(RoomParticipantService)
]
ChatMessageServiceDep = Annotated[ChatMessageService, Depends(ChatMessageService)]
BoardElementServiceDep = Annotated[BoardElementService, Depends(BoardElementService)]
BoardElementCommentServiceDep = Annotated[
    BoardElementCommentService, Depends(BoardElementCommentService)
]
PomodoroSessionServiceDep = Annotated[
    PomodoroSessionService, Depends(PomodoroSessionService)
]
RBACBootstrapServiceDep = Annotated[RBACBootstrapService, Depends(RBACBootstrapService)]
