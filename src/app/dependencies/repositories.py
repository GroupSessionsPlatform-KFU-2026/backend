from typing import Annotated

from fastapi import Depends

from src.app.dependencies.session import SessionDep
from src.app.models.board_element import BoardElement
from src.app.models.board_element_comment import BoardElementComment
from src.app.models.chat_message import ChatMessage
from src.app.models.pomodoro_session import PomodoroSession
from src.app.models.project import Project
from src.app.models.project_tag import ProjectTag
from src.app.models.refresh_session import RefreshSession
from src.app.models.room import Room
from src.app.models.room_participant import RoomParticipant
from src.app.models.tag import Tag
from src.app.models.user import User
from src.app.utils.repository import Repository


async def get_refresh_session_repository(session: SessionDep):
    yield Repository[RefreshSession](session)


type RefreshSessionRepository = Repository[RefreshSession]
RefreshSessionRepositoryDep = Annotated[
    RefreshSessionRepository, Depends(get_refresh_session_repository)
]


async def get_user_repository(session: SessionDep):
    yield Repository[User](session)


type UserRepository = Repository[User]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


async def get_project_repository(session: SessionDep):
    yield Repository[Project](session)


type ProjectRepository = Repository[Project]
ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


async def get_tag_repository(session: SessionDep):
    yield Repository[Tag](session)


type TagRepository = Repository[Tag]
TagRepositoryDep = Annotated[TagRepository, Depends(get_tag_repository)]


async def get_project_tag_repository(session: SessionDep):
    yield Repository[ProjectTag](session)


type ProjectTagRepository = Repository[ProjectTag]
ProjectTagRepositoryDep = Annotated[
    ProjectTagRepository, Depends(get_project_tag_repository)
]


async def get_room_repository(session: SessionDep):
    yield Repository[Room](session)


type RoomRepository = Repository[Room]
RoomRepositoryDep = Annotated[RoomRepository, Depends(get_room_repository)]


async def get_room_participant_repository(session: SessionDep):
    yield Repository[RoomParticipant](session)


type RoomParticipantRepository = Repository[RoomParticipant]
RoomParticipantRepositoryDep = Annotated[
    RoomParticipantRepository, Depends(get_room_participant_repository)
]


async def get_chat_message_repository(session: SessionDep):
    yield Repository[ChatMessage](session)


type ChatMessageRepository = Repository[ChatMessage]
ChatMessageRepositoryDep = Annotated[
    ChatMessageRepository, Depends(get_chat_message_repository)
]


async def get_board_element_repository(session: SessionDep):
    yield Repository[BoardElement](session)


type BoardElementRepository = Repository[BoardElement]
BoardElementRepositoryDep = Annotated[
    BoardElementRepository, Depends(get_board_element_repository)
]


async def get_board_element_comment_repository(session: SessionDep):
    yield Repository[BoardElementComment](session)


type BoardElementCommentRepository = Repository[BoardElementComment]
BoardElementCommentRepositoryDep = Annotated[
    BoardElementCommentRepository,
    Depends(get_board_element_comment_repository),
]


async def get_pomodoro_session_repository(session: SessionDep):
    yield Repository[PomodoroSession](session)


type PomodoroSessionRepository = Repository[PomodoroSession]
PomodoroSessionRepositoryDep = Annotated[
    PomodoroSessionRepository, Depends(get_pomodoro_session_repository)
]
