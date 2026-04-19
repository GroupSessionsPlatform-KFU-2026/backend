from contextlib import asynccontextmanager
from typing import AsyncIterator

from src.app.dependencies.session import async_session_maker
from src.app.models.board_element import BoardElement
from src.app.models.board_element_comment import BoardElementComment
from src.app.models.chat_message import ChatMessage
from src.app.models.pomodoro_session import PomodoroSession
from src.app.models.room import Room
from src.app.services.board_elements import BoardElementService
from src.app.services.board_elements_comments import BoardElementCommentService
from src.app.services.chat_messages import ChatMessageService
from src.app.services.pomodoro_sessions import PomodoroSessionService
from src.app.utils.repository import Repository


class SocketServiceFactory:
    @asynccontextmanager
    async def chat(self) -> AsyncIterator[tuple[Repository[Room], ChatMessageService]]:
        async with async_session_maker() as db_session:
            room_repository = Repository[Room](db_session)
            chat_repository = Repository[ChatMessage](db_session)
            yield room_repository, ChatMessageService(repository=chat_repository)

    @asynccontextmanager
    async def board(
        self,
    ) -> AsyncIterator[tuple[Repository[Room], BoardElementService]]:
        async with async_session_maker() as db_session:
            room_repository = Repository[Room](db_session)
            board_repository = Repository[BoardElement](db_session)
            yield room_repository, BoardElementService(repository=board_repository)

    @asynccontextmanager
    async def board_comments(
        self,
    ) -> AsyncIterator[tuple[Repository[Room], BoardElementCommentService]]:
        async with async_session_maker() as db_session:
            room_repository = Repository[Room](db_session)
            comment_repository = Repository[BoardElementComment](db_session)
            element_repository = Repository[BoardElement](db_session)
            yield (
                room_repository,
                BoardElementCommentService(
                    repository=comment_repository,
                    board_element_repository=element_repository,
                ),
            )

    @asynccontextmanager
    async def pomodoro(
        self,
    ) -> AsyncIterator[tuple[Repository[Room], PomodoroSessionService]]:
        async with async_session_maker() as db_session:
            room_repository = Repository[Room](db_session)
            pomodoro_repository = Repository[PomodoroSession](db_session)
            yield (
                room_repository,
                PomodoroSessionService(
                    repository=pomodoro_repository,
                ),
            )


socket_service_factory = SocketServiceFactory()
