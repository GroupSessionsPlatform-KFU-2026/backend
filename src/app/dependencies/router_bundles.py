from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.app.dependencies.services import (
    BoardElementCommentServiceDep,
    BoardElementServiceDep,
    ChatMessageServiceDep,
    RoomAccessServiceDep,
    RoomParticipantServiceDep,
)
from src.app.services.board_elements import BoardElementService
from src.app.services.board_elements_comments import BoardElementCommentService
from src.app.services.chat_messages import ChatMessageService
from src.app.services.room_access import RoomAccessService
from src.app.services.room_participants import RoomParticipantService


@dataclass(slots=True)
class MessageMutationDeps:
    chat_service: ChatMessageService
    room_access: RoomAccessService


def get_message_mutation_deps(
    chat_service: ChatMessageServiceDep,
    room_access: RoomAccessServiceDep,
) -> MessageMutationDeps:
    return MessageMutationDeps(
        chat_service=chat_service,
        room_access=room_access,
    )


MessageMutationDepsDep = Annotated[
    MessageMutationDeps,
    Depends(get_message_mutation_deps),
]


@dataclass(slots=True)
class BoardMutationDeps:
    board_service: BoardElementService
    room_access: RoomAccessService


def get_board_mutation_deps(
    board_service: BoardElementServiceDep,
    room_access: RoomAccessServiceDep,
) -> BoardMutationDeps:
    return BoardMutationDeps(
        board_service=board_service,
        room_access=room_access,
    )


BoardMutationDepsDep = Annotated[
    BoardMutationDeps,
    Depends(get_board_mutation_deps),
]


@dataclass(slots=True)
class BoardCommentMutationDeps:
    comment_service: BoardElementCommentService
    room_access: RoomAccessService


def get_board_comment_mutation_deps(
    comment_service: BoardElementCommentServiceDep,
    room_access: RoomAccessServiceDep,
) -> BoardCommentMutationDeps:
    return BoardCommentMutationDeps(
        comment_service=comment_service,
        room_access=room_access,
    )


BoardCommentMutationDepsDep = Annotated[
    BoardCommentMutationDeps,
    Depends(get_board_comment_mutation_deps),
]


@dataclass(slots=True)
class ParticipantMutationDeps:
    participant_service: RoomParticipantService
    room_access: RoomAccessService


def get_participant_mutation_deps(
    participant_service: RoomParticipantServiceDep,
    room_access: RoomAccessServiceDep,
) -> ParticipantMutationDeps:
    return ParticipantMutationDeps(
        participant_service=participant_service,
        room_access=room_access,
    )


ParticipantMutationDepsDep = Annotated[
    ParticipantMutationDeps,
    Depends(get_participant_mutation_deps),
]


@dataclass(slots=True)
class RoomElementPath:
    room_id: UUID
    element_id: UUID


RoomElementPathDep = Annotated[
    RoomElementPath,
    Depends(),
]
