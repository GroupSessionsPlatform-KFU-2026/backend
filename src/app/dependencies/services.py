from typing import Annotated

from fastapi import BackgroundTasks, Depends

<<<<<<< HEAD
from src.app.dependencies.repositories import (
    EmailNotificationRepositoryDep,
    RefreshSessionRepositoryDep,
    RoleRepositoryDep,
    UserRepositoryDep,
    UserRoleRepositoryDep,
)
<<<<<<< HEAD
from src.app.services.auth import AuthRepositories, AuthService
=======
=======
>>>>>>> 4ae6b89 (feature:dependency and service jwt)
from src.app.services.auth import AuthService
>>>>>>> a7a34d2 (feature:dependency and service jwt)
from src.app.services.board_elements import BoardElementService
from src.app.services.board_elements_comments import BoardElementCommentService
from src.app.services.chat_messages import ChatMessageService
from src.app.services.email import EmailService
from src.app.services.pomodoro_sessions import PomodoroSessionService
from src.app.services.projects import ProjectService
from src.app.services.rbac_bootstrap import RBACBootstrapService
from src.app.services.room_access import RoomAccessService
from src.app.services.room_participants import RoomParticipantService
from src.app.services.rooms import RoomService
from src.app.services.tags import TagService
from src.app.services.users import UserService

AuthServiceDep = Annotated[AuthService, Depends(AuthService)]
UserServiceDep = Annotated[UserService, Depends(UserService)]


def get_email_service(background_tasks: BackgroundTasks) -> EmailService:
    return EmailService(background_tasks)


EmailServiceDep = Annotated[EmailService, Depends(get_email_service)]


def get_auth_repositories(
    user_repository: UserRepositoryDep,
    refresh_session_repository: RefreshSessionRepositoryDep,
    role_repository: RoleRepositoryDep,
    user_role_repository: UserRoleRepositoryDep,
    email_notification_repository: EmailNotificationRepositoryDep,
) -> AuthRepositories:
    return AuthRepositories(
        user_repository=user_repository,
        refresh_session_repository=refresh_session_repository,
        role_repository=role_repository,
        user_role_repository=user_role_repository,
        email_notification_repository=email_notification_repository,
    )


AuthRepositoriesDep = Annotated[AuthRepositories, Depends(get_auth_repositories)]


def get_auth_service(
    repositories: AuthRepositoriesDep,
    user_service: UserServiceDep,
    email_service: EmailServiceDep,
) -> AuthService:
    return AuthService(
        repositories=repositories,
        user_service=user_service,
        email_service=email_service,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
RoomAccessServiceDep = Annotated[RoomAccessService, Depends(RoomAccessService)]
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
