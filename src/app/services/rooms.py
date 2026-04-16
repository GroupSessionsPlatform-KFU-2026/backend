import secrets
import string
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    PomodoroSessionRepositoryDep,
    RoomParticipantRepository,
    RoomParticipantRepositoryDep,
    RoomRepository,
    RoomRepositoryDep,
)
from src.app.models.pomodoro_session import PomodoroSessionCreate
from src.app.models.room import Room, RoomCreate, RoomStatus, RoomUpdate
from src.app.models.room_participant import RoomParticipant
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_request import JoinRoomRequest
from src.app.services.pomodoro_sessions import PomodoroSessionService


def generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class RoomService:
    __room_repository: RoomRepository
    __room_participant_repository: RoomParticipantRepository
    __pomodoro_service: PomodoroSessionService

    def __init__(
        self,
        room_repository: RoomRepositoryDep,
        room_participant_repository: RoomParticipantRepositoryDep,
        pomodoro_repository: PomodoroSessionRepositoryDep,
    ):
        self.__room_repository = room_repository
        self.__room_participant_repository = room_participant_repository
        self.__pomodoro_service = PomodoroSessionService(repository=pomodoro_repository)

    async def get_rooms(self, filters: RoomFilters) -> Sequence[Room]:
        return await self.__room_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_room(self, room_create: RoomCreate) -> Room:
        room_dump = room_create.model_dump()

        room = Room(
            **room_dump,
            room_code=generate_room_code(),
            status=RoomStatus.ACTIVE,
            ended_at=None,
        )

        # TODO: creator_id should come from OAuth current user later.
        created_room = await self.__room_repository.save(room)

        await self.__pomodoro_service.create_pomodoro(
            PomodoroSessionCreate(
                room_id=created_room.id,
                work_duration=25,
                short_break_duration=5,
                long_break_duration=15,
                cycles_before_long=4,
            )
        )

        return created_room

    async def get_room(self, room_id: UUID) -> Optional[Room]:
        return await self.__room_repository.get(room_id)

    async def update_room(
        self,
        room_update: RoomUpdate,
        room_id: UUID,
    ) -> Optional[Room]:
        # TODO: add ownership validation after auth is implemented.
        return await self.__room_repository.update(room_id, room_update)

    async def end_room(self, room_id: UUID) -> Optional[Room]:
        room = await self.__room_repository.get(room_id)
        if room is None:
            return None

        room.status = RoomStatus.ENDED
        room.ended_at = datetime.now(timezone.utc)
        return await self.__room_repository.save(room)

    async def join_room(self, payload: JoinRoomRequest) -> Optional[RoomParticipant]:
        # TODO: user_id should come from OAuth current user later.
        room = await self.__room_repository.get_one_by_filters(
            extra_filters={'room_code': payload.room_code},
        )
        if room is None:
            return None

        participant = RoomParticipant(
            room_id=room.id,
            user_id=payload.user_id,
            role='participant',
            joined_at=datetime.now(timezone.utc),
            left_at=None,
            is_kicked=False,
        )
        return await self.__room_participant_repository.save(participant)
